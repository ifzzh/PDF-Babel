from collections import deque
import threading
from typing import Deque

from backend import queue_store


class JobScheduler:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queue: Deque[str] = deque()
        self._running: set[str] = set()
        self._max_running = 1

    def configure(self, max_running: int) -> None:
        with self._lock:
            self._max_running = max(1, int(max_running))

    def submit(self, job_id: str, settings, storage) -> str:
        with self._lock:
            if job_id in self._running:
                return "running"
            if job_id in self._queue:
                return "queued"
            self._queue.append(job_id)
        queue_store.enqueue_job(settings, job_id)
        self._try_dispatch(settings, storage)
        with self._lock:
            return "running" if job_id in self._running else "queued"

    def cancel(self, settings, job_id: str) -> bool:
        with self._lock:
            if job_id in self._queue:
                self._queue.remove(job_id)
                queue_store.remove_job(settings, job_id)
                return True
        return False

    def snapshot(self) -> dict[str, list[str] | int]:
        with self._lock:
            return {
                "max_running": self._max_running,
                "running": list(self._running),
                "queued": list(self._queue),
            }

    def dispatch(self, settings, storage) -> None:
        self._try_dispatch(settings, storage)

    def _try_dispatch(self, settings, storage) -> None:
        start_jobs: list[str] = []
        with self._lock:
            while self._queue and len(self._running) < self._max_running:
                job_id = self._queue.popleft()
                if job_id in self._running:
                    continue
                self._running.add(job_id)
                queue_store.mark_running(settings, job_id)
                start_jobs.append(job_id)

        for job_id in start_jobs:
            threading.Thread(
                target=self._run_job,
                args=(job_id, settings, storage),
                daemon=True,
            ).start()

    def _run_job(self, job_id: str, settings, storage) -> None:
        from backend.translator import run_translation_job

        try:
            run_translation_job(settings, storage, job_id)
        except Exception:
            pass
        finally:
            self._mark_done(job_id, settings, storage)

    def _mark_done(self, job_id: str, settings, storage) -> None:
        with self._lock:
            self._running.discard(job_id)
            queue_store.remove_job(settings, job_id)
        self._try_dispatch(settings, storage)

    def load_queued(self, job_ids: list[str]) -> None:
        with self._lock:
            for job_id in job_ids:
                if job_id not in self._queue and job_id not in self._running:
                    self._queue.append(job_id)


SCHEDULER = JobScheduler()

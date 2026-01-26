from collections import deque
from dataclasses import dataclass
from datetime import datetime
import threading
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Asia/Shanghai")
_MAX_EVENTS = 2000


def _now_iso() -> str:
    return datetime.now(tz=_TZ).isoformat(timespec="seconds")


@dataclass
class _JobEvents:
    cond: threading.Condition
    events: deque
    next_id: int
    cancel_event: threading.Event | None = None
    running: bool = False


class JobEventStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _JobEvents] = {}
        self._running_count = 0

    def _ensure_job_locked(self, job_id: str) -> _JobEvents:
        job = self._jobs.get(job_id)
        if job is None:
            job = _JobEvents(
                cond=threading.Condition(),
                events=deque(maxlen=_MAX_EVENTS),
                next_id=1,
                cancel_event=None,
            )
            self._jobs[job_id] = job
        return job

    def _ensure_job(self, job_id: str) -> _JobEvents:
        with self._lock:
            return self._ensure_job_locked(job_id)

    def set_cancel_event(self, job_id: str, cancel_event: threading.Event) -> None:
        job = self._ensure_job(job_id)
        with job.cond:
            job.cancel_event = cancel_event
            job.cond.notify_all()

    def get_cancel_event(self, job_id: str) -> threading.Event | None:
        job = self._ensure_job(job_id)
        return job.cancel_event

    def append_event(self, job_id: str, event_type: str, data: dict) -> dict:
        job = self._ensure_job(job_id)
        with job.cond:
            event_id = job.next_id
            job.next_id += 1
            payload = {
                "id": event_id,
                "type": event_type,
                "job_id": job_id,
                "ts": _now_iso(),
                "data": data,
            }
            job.events.append(payload)
            job.cond.notify_all()
            return payload

    def try_acquire_slot(self, job_id: str, max_running: int) -> str:
        with self._lock:
            job = self._ensure_job_locked(job_id)
            if job.running:
                return "running"
            if max_running > 0 and self._running_count >= max_running:
                return "limit"
            job.running = True
            self._running_count += 1
            return "ok"

    def try_mark_running(self, job_id: str) -> bool:
        job = self._ensure_job(job_id)
        with job.cond:
            if job.running:
                return False
            job.running = True
            return True

    def clear_running(self, job_id: str) -> None:
        with self._lock:
            job = self._ensure_job_locked(job_id)
            if job.running:
                job.running = False
                if self._running_count > 0:
                    self._running_count -= 1
        with job.cond:
            job.cond.notify_all()

    def wait_for_events(
        self, job_id: str, last_id: int, timeout: float
    ) -> list[dict]:
        job = self._ensure_job(job_id)
        with job.cond:
            pending = [e for e in job.events if e["id"] > last_id]
            if pending:
                return pending
            job.cond.wait(timeout=timeout)
            return [e for e in job.events if e["id"] > last_id]


EVENT_STORE = JobEventStore()

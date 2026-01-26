from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo

from backend.config import Settings

_TZ = ZoneInfo("Asia/Shanghai")


def _now_iso() -> str:
    return datetime.now(tz=_TZ).isoformat(timespec="seconds")


def enqueue_job(settings: Settings, job_id: str) -> None:
    now = _now_iso()
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            """
            INSERT INTO job_queue (job_id, status, enqueued_at, updated_at)
            VALUES (?, 'queued', ?, ?)
            ON CONFLICT(job_id) DO NOTHING
            """,
            (job_id, now, now),
        )
        conn.commit()
    finally:
        conn.close()


def mark_running(settings: Settings, job_id: str) -> None:
    now = _now_iso()
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            "UPDATE job_queue SET status='running', updated_at=? WHERE job_id=?",
            (now, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def remove_job(settings: Settings, job_id: str) -> None:
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute("DELETE FROM job_queue WHERE job_id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()


def snapshot(settings: Settings) -> dict[str, list[str]]:
    conn = sqlite3.connect(settings.db_path)
    try:
        queued_rows = conn.execute(
            "SELECT job_id FROM job_queue WHERE status='queued' ORDER BY enqueue_seq"
        ).fetchall()
        running_rows = conn.execute(
            "SELECT job_id FROM job_queue WHERE status='running' ORDER BY enqueue_seq"
        ).fetchall()
    finally:
        conn.close()
    return {
        "queued": [row[0] for row in queued_rows],
        "running": [row[0] for row in running_rows],
    }


def reset_running_to_queued(settings: Settings) -> None:
    now = _now_iso()
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            "UPDATE job_queue SET status='queued', updated_at=? WHERE status='running'",
            (now,),
        )
        conn.execute(
            "UPDATE jobs SET status='queued', updated_at=? WHERE status='running'",
            (now,),
        )
        conn.commit()
    finally:
        conn.close()

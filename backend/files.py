from dataclasses import dataclass
from datetime import datetime
import sqlite3
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.config import Settings

_TZ = ZoneInfo("Asia/Shanghai")


@dataclass(frozen=True)
class FileRecord:
    id: str
    job_id: str
    type: str
    watermark: str | None
    filename: str
    path: str
    size: int
    created_at: str


def _now_iso() -> str:
    return datetime.now(tz=_TZ).isoformat(timespec="seconds")


def create_file_record(
    settings: Settings,
    job_id: str,
    file_type: str,
    watermark: str | None,
    filename: str,
    path: Path,
) -> FileRecord:
    record = FileRecord(
        id=str(uuid4()),
        job_id=job_id,
        type=file_type,
        watermark=watermark,
        filename=filename,
        path=str(path),
        size=path.stat().st_size,
        created_at=_now_iso(),
    )
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            """
            INSERT INTO files (
                id, job_id, type, watermark, filename, path, size, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.job_id,
                record.type,
                record.watermark,
                record.filename,
                record.path,
                record.size,
                record.created_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return record


def list_files_by_job(settings: Settings, job_id: str) -> list[FileRecord]:
    conn = sqlite3.connect(settings.db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, job_id, type, watermark, filename, path, size, created_at
            FROM files
            WHERE job_id = ?
            ORDER BY created_at ASC
            """,
            (job_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        FileRecord(
            id=row[0],
            job_id=row[1],
            type=row[2],
            watermark=row[3],
            filename=row[4],
            path=row[5],
            size=row[6],
            created_at=row[7],
        )
        for row in rows
    ]


def get_file_by_id(settings: Settings, file_id: str) -> FileRecord | None:
    conn = sqlite3.connect(settings.db_path)
    try:
        row = conn.execute(
            """
            SELECT id, job_id, type, watermark, filename, path, size, created_at
            FROM files
            WHERE id = ?
            """,
            (file_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return FileRecord(
        id=row[0],
        job_id=row[1],
        type=row[2],
        watermark=row[3],
        filename=row[4],
        path=row[5],
        size=row[6],
        created_at=row[7],
    )


def get_file_flags(
    settings: Settings, job_ids: list[str]
) -> dict[str, tuple[bool, bool]]:
    if not job_ids:
        return {}
    placeholders = ",".join("?" for _ in job_ids)
    sql = (
        "SELECT job_id, "
        "MAX(CASE WHEN type = 'mono' THEN 1 ELSE 0 END) AS has_mono, "
        "MAX(CASE WHEN type = 'dual' THEN 1 ELSE 0 END) AS has_dual, "
        "MAX(CASE WHEN type = 'glossary' THEN 1 ELSE 0 END) AS has_glossary "
        f"FROM files WHERE job_id IN ({placeholders}) GROUP BY job_id"
    )
    conn = sqlite3.connect(settings.db_path)
    try:
        rows = conn.execute(sql, job_ids).fetchall()
    finally:
        conn.close()
    return {
        row[0]: (bool(row[1]), bool(row[2]), bool(row[3])) for row in rows
    }

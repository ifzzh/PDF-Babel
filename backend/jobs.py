from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.config import Settings

_TZ = ZoneInfo("Asia/Shanghai")


@dataclass(frozen=True)
class JobRecord:
    id: str
    folder_name: str
    original_filename: str
    created_at: str
    updated_at: str
    status: str
    options_json: str | None
    source_json: str | None
    error: str | None


def _now_iso() -> str:
    return datetime.now(tz=_TZ).isoformat(timespec="seconds")


def _unique_folder_name(jobs_dir: Path, base_name: str) -> str:
    candidate = base_name
    if not (jobs_dir / candidate).exists():
        return candidate
    for _ in range(20):
        suffix = uuid4().hex[:4]
        candidate = f"{base_name}_{suffix}"
        if not (jobs_dir / candidate).exists():
            return candidate
    raise RuntimeError("failed to allocate unique folder name")


def create_job(
    settings: Settings,
    jobs_dir: Path,
    original_filename: str,
    file_bytes: bytes,
    options: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
) -> JobRecord:
    safe_name = Path(original_filename).name
    stem = Path(safe_name).stem or "document"
    folder_name = _unique_folder_name(jobs_dir, stem)
    job_dir = jobs_dir / folder_name
    job_dir.mkdir(parents=True, exist_ok=False)
    original_path = job_dir / safe_name
    original_path.write_bytes(file_bytes)

    job_id = str(uuid4())
    created_at = _now_iso()
    record = JobRecord(
        id=job_id,
        folder_name=folder_name,
        original_filename=safe_name,
        created_at=created_at,
        updated_at=created_at,
        status="queued",
        options_json=json.dumps(options, ensure_ascii=False) if options else None,
        source_json=json.dumps(source, ensure_ascii=False) if source else None,
        error=None,
    )

    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            """
            INSERT INTO jobs (
                id, folder_name, original_filename, created_at, updated_at,
                status, options_json, source_json, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.folder_name,
                record.original_filename,
                record.created_at,
                record.updated_at,
                record.status,
                record.options_json,
                record.source_json,
                record.error,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return record


def get_job_by_id(settings: Settings, job_id: str) -> JobRecord | None:
    conn = sqlite3.connect(settings.db_path)
    try:
        row = conn.execute(
            """
            SELECT id, folder_name, original_filename, created_at, updated_at,
                   status, options_json, source_json, error
            FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return JobRecord(
        id=row[0],
        folder_name=row[1],
        original_filename=row[2],
        created_at=row[3],
        updated_at=row[4],
        status=row[5],
        options_json=row[6],
        source_json=row[7],
        error=row[8],
    )


def list_jobs(
    settings: Settings,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[JobRecord], int]:
    clauses = []
    params: list = []
    if created_from:
        clauses.append("created_at >= ?")
        params.append(created_from)
    if created_to:
        clauses.append("created_at <= ?")
        params.append(created_to)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    count_sql = f"SELECT COUNT(1) FROM jobs {where_sql}"
    list_sql = (
        "SELECT id, folder_name, original_filename, created_at, updated_at, "
        "status, options_json, source_json, error "
        f"FROM jobs {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    )
    conn = sqlite3.connect(settings.db_path)
    try:
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(list_sql, [*params, limit, offset]).fetchall()
    finally:
        conn.close()
    items = [
        JobRecord(
            id=row[0],
            folder_name=row[1],
            original_filename=row[2],
            created_at=row[3],
            updated_at=row[4],
            status=row[5],
            options_json=row[6],
            source_json=row[7],
            error=row[8],
        )
        for row in rows
    ]
    return items, total

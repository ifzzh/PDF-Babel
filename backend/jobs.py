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


def _folder_timestamp() -> str:
    return datetime.now(tz=_TZ).strftime("%Y%m%d-%H%M%S")


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
    folder_base = f"{_folder_timestamp()}_{stem}"
    folder_name = _unique_folder_name(jobs_dir, folder_base)
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

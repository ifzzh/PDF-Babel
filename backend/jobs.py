from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.config import Settings
from backend.files import create_file_record

_TZ = ZoneInfo("Asia/Shanghai")
_INVALID_CHARS = set('/\\:*?"<>|')


@dataclass(frozen=True)
class JobRecord:
    id: str
    folder_name: str
    original_filename: str
    created_at: str
    updated_at: str
    renamed_at: str | None
    status: str
    options_json: str | None
    source_json: str | None
    error: str | None


def _now_iso() -> str:
    return datetime.now(tz=_TZ).isoformat(timespec="seconds")


def _time_suffix() -> str:
    return datetime.now(tz=_TZ).strftime("%Y%m%d-%H%M%S")


def _validate_name(value: str, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is empty")
    if Path(cleaned).name != cleaned:
        raise ValueError(f"{field_name} contains path separators")
    for ch in cleaned:
        if ch in _INVALID_CHARS or ord(ch) < 32:
            raise ValueError(f"{field_name} contains invalid characters")
    return cleaned


def _normalize_folder_name(value: str) -> str:
    return _validate_name(value, "folder_name")


def _normalize_original_filename(value: str) -> str:
    name = _validate_name(value, "original_filename")
    if Path(name).suffix == "":
        name = f"{name}.pdf"
    if Path(name).suffix.lower() != ".pdf":
        raise ValueError("original_filename must end with .pdf")
    return name


def _suggest_folder_name(base_name: str) -> str:
    return f"{base_name}_{_time_suffix()}"


def _suggest_filename(name: str) -> str:
    stem = Path(name).stem or "document"
    suffix = Path(name).suffix or ".pdf"
    return f"{stem}_{_time_suffix()}{suffix}"


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
        renamed_at=None,
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
                renamed_at, status, options_json, source_json, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.folder_name,
                record.original_filename,
                record.created_at,
                record.updated_at,
                record.renamed_at,
                record.status,
                record.options_json,
                record.source_json,
                record.error,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    create_file_record(
        settings,
        job_id=record.id,
        file_type="original",
        watermark="none",
        filename=safe_name,
        path=original_path,
    )

    return record


def get_job_by_id(settings: Settings, job_id: str) -> JobRecord | None:
    conn = sqlite3.connect(settings.db_path)
    try:
        row = conn.execute(
            """
            SELECT id, folder_name, original_filename, created_at, updated_at,
                   renamed_at, status, options_json, source_json, error
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
        renamed_at=row[5],
        status=row[6],
        options_json=row[7],
        source_json=row[8],
        error=row[9],
    )


def update_job_status(
    settings: Settings,
    job_id: str,
    status: str,
    error: str | None = None,
) -> JobRecord | None:
    updated_at = _now_iso()
    conn = sqlite3.connect(settings.db_path)
    try:
        if error is None:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                (status, updated_at, job_id),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, error = ? WHERE id = ?",
                (status, updated_at, error, job_id),
            )
        conn.commit()
    finally:
        conn.close()
    return get_job_by_id(settings, job_id)


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
        "renamed_at, status, options_json, source_json, error "
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
            renamed_at=row[5],
            status=row[6],
            options_json=row[7],
            source_json=row[8],
            error=row[9],
        )
        for row in rows
    ]
    return items, total


def rename_job(
    settings: Settings,
    jobs_dir: Path,
    job_id: str,
    folder_name: str | None,
    original_filename: str | None,
    confirm: bool,
) -> tuple[JobRecord, dict[str, str] | None]:
    record = get_job_by_id(settings, job_id)
    if record is None:
        raise ValueError("job not found")
    if record.status not in ("finished", "failed", "canceled"):
        raise PermissionError("rename_not_allowed")

    new_folder_name = record.folder_name
    new_original_filename = record.original_filename
    if folder_name is not None:
        new_folder_name = _normalize_folder_name(folder_name)
    if original_filename is not None:
        new_original_filename = _normalize_original_filename(original_filename)

    if (
        new_folder_name == record.folder_name
        and new_original_filename == record.original_filename
    ):
        return record, None

    current_dir = jobs_dir / record.folder_name
    target_dir = jobs_dir / new_folder_name
    current_file = current_dir / record.original_filename
    target_file = target_dir / new_original_filename

    suggestions: dict[str, str] = {}
    conflict = False
    if new_folder_name != record.folder_name and target_dir.exists():
        conflict = True
        suggestions["folder_name"] = _suggest_folder_name(new_folder_name)
    if target_file.exists() and target_file != current_file:
        conflict = True
        suggestions["original_filename"] = _suggest_filename(
            new_original_filename
        )

    if conflict and not confirm:
        return record, suggestions
    if conflict and confirm:
        return record, suggestions

    if new_original_filename != record.original_filename:
        current_file.rename(current_dir / new_original_filename)
    if new_folder_name != record.folder_name:
        current_dir.rename(target_dir)

    renamed_at = _now_iso()
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.execute(
            """
            UPDATE jobs
            SET folder_name = ?, original_filename = ?, updated_at = ?, renamed_at = ?
            WHERE id = ?
            """,
            (
                new_folder_name,
                new_original_filename,
                renamed_at,
                renamed_at,
                record.id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    updated = get_job_by_id(settings, record.id)
    return updated, None

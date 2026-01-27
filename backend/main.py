import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
import re
import shutil

from backend.config import settings
from backend.channels import get_channels
from backend.db import init_db
from backend.jobs import create_job
from backend.jobs import get_job_by_id
from backend.jobs import list_jobs
from backend.jobs import rename_job
from backend.jobs import update_job_status
from backend.jobs import delete_job_records
from backend.files import create_file_record
from backend.files import get_file_by_id
from backend.files import get_file_flags
from backend.files import list_files_by_job
from backend.storage import ensure_storage
from backend.events import EVENT_STORE
from backend.scheduler import SCHEDULER
from backend import queue_store

app = FastAPI()
app.state.settings = settings


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/channels")
def channels():
    return get_channels(app.state.settings)


def _parse_json(value: str, field_name: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"invalid {field_name} json"
        ) from exc


def _validate_source(source: dict):
    mode = source.get("mode")
    if mode not in ("platform", "custom"):
        raise HTTPException(status_code=400, detail="invalid source.mode")
    channel_id = source.get("channel_id")
    if not channel_id:
        raise HTTPException(status_code=400, detail="missing source.channel_id")
    channels = get_channels(app.state.settings)
    pool = channels.get(mode, [])
    channel = next((c for c in pool if c.get("id") == channel_id), None)
    if channel is None:
        raise HTTPException(status_code=400, detail="unsupported channel_id")
    if not channel.get("visible", True):
        raise HTTPException(status_code=400, detail="channel not visible")
    if not channel.get("enabled", True):
        raise HTTPException(status_code=400, detail="channel disabled")
    return channel


def _normalize_bool(value: object, field: str) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
    raise HTTPException(status_code=400, detail=f"invalid options.{field}")


def _normalize_int(value: object, field: str, *, min_value: int | None = None) -> int:
    if value is None:
        raise HTTPException(status_code=400, detail=f"invalid options.{field}")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid options.{field}") from exc
    if min_value is not None and parsed < min_value:
        raise HTTPException(
            status_code=400,
            detail=f"options.{field} must be >= {min_value}",
        )
    return parsed


def _normalize_enum(value: object, field: str, allowed: set[str]) -> str:
    if value is None:
        raise HTTPException(status_code=400, detail=f"invalid options.{field}")
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"invalid options.{field}")
    if value not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"invalid options.{field}",
        )
    return value


def _validate_options(options: dict) -> dict:
    bool_fields = (
        "no_dual",
        "no_mono",
        "split_short_lines",
        "skip_clean",
        "enhance_compatibility",
        "disable_rich_text_translate",
        "skip_scanned_detection",
        "ocr_workaround",
        "auto_enable_ocr_workaround",
        "auto_extract_glossary",
        "save_auto_extracted_glossary",
        "add_formula_placehold_hint",
        "disable_same_text_fallback",
        "only_include_translated_page",
    )
    for field in bool_fields:
        if field in options:
            options[field] = _normalize_bool(options.get(field), field)

    if "qps" in options:
        options["qps"] = _normalize_int(options.get("qps"), "qps", min_value=1)

    if "max_pages_per_part" in options:
        options["max_pages_per_part"] = _normalize_int(
            options.get("max_pages_per_part"),
            "max_pages_per_part",
            min_value=0,
        )

    if "watermark_output_mode" in options:
        options["watermark_output_mode"] = _normalize_enum(
            options.get("watermark_output_mode"),
            "watermark_output_mode",
            {"watermarked", "no_watermark"},
        )

    if "primary_font_family" in options:
        options["primary_font_family"] = _normalize_enum(
            options.get("primary_font_family"),
            "primary_font_family",
            {"serif", "sans-serif", "script"},
        )

    if options.get("no_dual") is True and options.get("no_mono") is True:
        raise HTTPException(
            status_code=400,
            detail="invalid options: no_dual and no_mono cannot both be true",
        )

    return options


def _format_sse(event: dict) -> str:
    data = json.dumps(event, ensure_ascii=False)
    if "id" in event:
        return f"id: {event['id']}\ndata: {data}\n\n"
    return f"data: {data}\n\n"


_SSE_TZ = ZoneInfo("Asia/Shanghai")


@app.post("/api/jobs")
async def create_job_endpoint(
    file: UploadFile = File(...),
    options: str = Form(...),
    source: str = Form(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="file must be a pdf")
    options_obj = _parse_json(options, "options") if options else {}
    source_obj = _parse_json(source, "source") if source else {}
    _validate_source(source_obj)
    _validate_options(options_obj)
    if source_obj.get("mode") == "platform":
        source_obj.pop("credentials", None)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")
    record = create_job(
        app.state.settings,
        app.state.storage["jobs"],
        file.filename,
        content,
        options_obj,
        source_obj,
    )
    queue_store.enqueue_job(app.state.settings, record.id)
    return {
        "job_id": record.id,
        "status": record.status,
        "created_at": record.created_at,
    }


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": record.id,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "renamed_at": record.renamed_at,
        "folder_name": record.folder_name,
        "display_name": record.display_name,
        "original_filename": record.original_filename,
    }


def _safe_job_dir(storage_root: Path, folder_name: str) -> Path:
    root = storage_root.resolve()
    job_dir = (root / folder_name).resolve()
    if root not in job_dir.parents and job_dir != root:
        raise RuntimeError("invalid job directory")
    return job_dir


@app.get("/api/jobs/{job_id}/events")
def job_events(job_id: str):
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")

    def _event_stream():
        last_id = 0
        finished = False
        while True:
            events = EVENT_STORE.wait_for_events(job_id, last_id, timeout=2.0)
            if events:
                for event in events:
                    last_id = event["id"]
                    yield _format_sse(event)
                    if event.get("type") in ("finish", "error"):
                        finished = True
                if finished:
                    break
                continue

            current = get_job_by_id(app.state.settings, job_id)
            if current and current.status in ("finished", "failed", "canceled"):
                event_type = (
                    "finish" if current.status == "finished" else "error"
                )
                payload = EVENT_STORE.append_event(
                    job_id,
                    event_type,
                    {"status": current.status},
                )
                yield _format_sse(payload)
                break

            heartbeat = {
                "type": "heartbeat",
                "job_id": job_id,
                "ts": datetime.now(tz=_SSE_TZ).isoformat(timespec="seconds"),
                "data": {},
            }
            yield _format_sse(heartbeat)

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.post("/api/jobs/{job_id}/run")
def run_job(job_id: str):
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    if record.status != "queued":
        raise HTTPException(status_code=409, detail="job not queued")
    SCHEDULER.configure(app.state.settings.max_running)
    status = SCHEDULER.submit(record.id, app.state.settings, app.state.storage)
    return {"job_id": record.id, "status": status}


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    if record.status in ("finished", "failed", "canceled"):
        raise HTTPException(status_code=409, detail="job already finalized")
    if record.status == "queued":
        SCHEDULER.cancel(app.state.settings, record.id)
        update_job_status(
            app.state.settings, record.id, "canceled", error="canceled"
        )
        EVENT_STORE.append_event(
            record.id, "error", {"error": "canceled"}
        )
        return {"job_id": record.id, "status": "canceled"}

    cancel_event = EVENT_STORE.get_cancel_event(record.id)
    if cancel_event is None:
        raise HTTPException(status_code=409, detail="cancel_not_supported")
    cancel_event.set()
    return {"job_id": record.id, "status": "canceling"}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, confirm: bool = False, payload: dict | None = None):
    confirm_flag = bool(payload.get("confirm")) if payload else confirm
    if not confirm_flag:
        raise HTTPException(status_code=400, detail="confirm_required")
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")

    if record.status == "running":
        cancel_event = EVENT_STORE.get_cancel_event(record.id)
        if cancel_event is None:
            raise HTTPException(status_code=409, detail="cancel_not_supported")
        cancel_event.set()
        return {"job_id": record.id, "status": "canceling"}

    if record.status == "queued":
        SCHEDULER.cancel(app.state.settings, record.id)
        queue_store.remove_job(app.state.settings, record.id)

    job_dir = _safe_job_dir(app.state.storage["jobs"], record.folder_name)
    if job_dir.exists():
        shutil.rmtree(job_dir)

    delete_job_records(app.state.settings, record.id)
    queue_store.remove_job(app.state.settings, record.id)
    return {"job_id": record.id, "status": "deleted"}


@app.post("/api/jobs/delete")
def delete_jobs(payload: dict):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    job_ids = payload.get("job_ids")
    confirm = bool(payload.get("confirm", False))
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm_required")
    if not isinstance(job_ids, list) or not job_ids:
        raise HTTPException(status_code=400, detail="invalid job_ids")

    deleted: list[str] = []
    skipped: list[dict[str, str]] = []

    for job_id in job_ids:
        if not isinstance(job_id, str) or not job_id:
            skipped.append({"job_id": str(job_id), "reason": "invalid_id"})
            continue
        record = get_job_by_id(app.state.settings, job_id)
        if record is None:
            skipped.append({"job_id": job_id, "reason": "not_found"})
            continue
        if record.status == "running":
            cancel_event = EVENT_STORE.get_cancel_event(record.id)
            if cancel_event is None:
                skipped.append({"job_id": job_id, "reason": "cancel_not_supported"})
                continue
            cancel_event.set()
            skipped.append({"job_id": job_id, "reason": "canceling"})
            continue

        if record.status == "queued":
            SCHEDULER.cancel(app.state.settings, record.id)
            queue_store.remove_job(app.state.settings, record.id)

        job_dir = _safe_job_dir(app.state.storage["jobs"], record.folder_name)
        if job_dir.exists():
            shutil.rmtree(job_dir)

        delete_job_records(app.state.settings, record.id)
        queue_store.remove_job(app.state.settings, record.id)
        deleted.append(job_id)

    return {"deleted": deleted, "skipped": skipped}


@app.get("/api/queue")
def get_queue():
    SCHEDULER.configure(app.state.settings.max_running)
    snapshot = queue_store.snapshot(app.state.settings)
    return {
        "max_running": app.state.settings.max_running,
        "running": snapshot["running"],
        "queued": snapshot["queued"],
    }


@app.post("/api/queue/resume")
def resume_queue(payload: dict):
    mode = payload.get("mode")
    job_ids = payload.get("job_ids")
    if mode is None and job_ids is None:
        raise HTTPException(status_code=400, detail="missing mode/job_ids")
    if mode not in (None, "all"):
        raise HTTPException(status_code=400, detail="invalid mode")
    if mode == "all" and job_ids is not None:
        raise HTTPException(status_code=400, detail="mode conflicts with job_ids")
    if job_ids is not None:
        if not isinstance(job_ids, list) or not job_ids:
            raise HTTPException(status_code=400, detail="invalid job_ids")
        for item in job_ids:
            if not isinstance(item, str) or not item:
                raise HTTPException(status_code=400, detail="invalid job_ids")

    snapshot = queue_store.snapshot(app.state.settings)
    queued = snapshot["queued"]
    queued_set = set(queued)
    running_set = set(snapshot["running"])

    accepted: list[str] = []
    skipped: list[dict[str, str]] = []

    if mode == "all":
        accepted = queued
    else:
        want = set(job_ids or [])
        seen: set[str] = set()
        for job_id in queued:
            if job_id in want and job_id not in seen:
                accepted.append(job_id)
                seen.add(job_id)
        for job_id in job_ids or []:
            if job_id in seen:
                continue
            if job_id in running_set:
                skipped.append({"job_id": job_id, "reason": "running"})
            elif job_id not in queued_set:
                skipped.append({"job_id": job_id, "reason": "not_queued"})

    if accepted:
        SCHEDULER.load_queued(accepted)
        SCHEDULER.configure(app.state.settings.max_running)
        SCHEDULER.dispatch(app.state.settings, app.state.storage)

    return {"accepted": accepted, "skipped": skipped}


@app.get("/api/jobs")
def list_jobs_endpoint(
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="invalid limit")
    if offset < 0:
        raise HTTPException(status_code=400, detail="invalid offset")
    items, total = list_jobs(
        app.state.settings,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )
    flags = get_file_flags(app.state.settings, [job.id for job in items])
    return {
        "items": [
            {
                "job_id": job.id,
                "folder_name": job.folder_name,
                "display_name": job.display_name,
                "created_at": job.created_at,
                "renamed_at": job.renamed_at,
                "status": job.status,
                "has_mono": flags.get(job.id, (False, False, False))[0],
                "has_dual": flags.get(job.id, (False, False, False))[1],
                "has_glossary": flags.get(job.id, (False, False, False))[2],
            }
            for job in items
        ],
        "total": total,
    }


@app.patch("/api/jobs/{job_id}")
def rename_job_endpoint(job_id: str, payload: dict):
    folder_name = payload.get("folder_name")
    original_filename = payload.get("original_filename")
    display_name = payload.get("display_name")
    confirm = bool(payload.get("confirm", False))
    if folder_name is None and original_filename is None and display_name is None:
        raise HTTPException(status_code=400, detail="no changes provided")
    try:
        record, suggestions = rename_job(
            app.state.settings,
            app.state.storage["jobs"],
            job_id,
            folder_name,
            original_filename,
            display_name,
            confirm,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if suggestions:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "name_conflict",
                "suggested_folder_name": suggestions.get("folder_name"),
                "suggested_original_filename": suggestions.get("original_filename"),
            },
        )
    if record is None:
        raise HTTPException(status_code=500, detail="rename failed")
    return {
        "job_id": record.id,
        "folder_name": record.folder_name,
        "display_name": record.display_name,
        "original_filename": record.original_filename,
        "renamed_at": record.renamed_at,
        "updated_at": record.updated_at,
    }


@app.get("/api/jobs/{job_id}/files")
def get_job_files(job_id: str):
    record = get_job_by_id(app.state.settings, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    files = list_files_by_job(app.state.settings, job_id)
    if not files:
        original_path = (
            app.state.storage["jobs"] / record.folder_name / record.original_filename
        )
        if original_path.exists():
            create_file_record(
                app.state.settings,
                job_id=record.id,
                file_type="original",
                watermark="none",
                filename=record.original_filename,
                path=original_path,
            )
            files = list_files_by_job(app.state.settings, job_id)
    return [
        {
            "file_id": f.id,
            "type": f.type,
            "watermark": f.watermark,
            "filename": record.original_filename
            if f.type == "original"
            else f.filename,
            "size": (
                (
                    (
                        app.state.storage["jobs"]
                        / record.folder_name
                        / (
                            record.original_filename
                            if f.type == "original"
                            else f.filename
                        )
                    ).stat().st_size
                )
                if (
                    app.state.storage["jobs"]
                    / record.folder_name
                    / (
                        record.original_filename
                        if f.type == "original"
                        else f.filename
                    )
                ).exists()
                else f.size
            ),
            "url": f"/api/files/{f.id}",
        }
        for f in files
    ]


def _iter_file_range(path, start: int, end: int, chunk_size: int = 1024 * 1024):
    with path.open("rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = f.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@app.get("/api/files/{file_id}")
def download_file(file_id: str, request: Request):
    record = get_file_by_id(app.state.settings, file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="file not found")
    job = get_job_by_id(app.state.settings, record.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    stem = Path(job.original_filename).stem
    if record.type == "original":
        download_name = job.original_filename
        disk_name = job.original_filename
    elif record.type == "mono":
        download_name = f"{stem}.mono.pdf"
        disk_name = record.filename
    elif record.type == "dual":
        download_name = f"{stem}.dual.pdf"
        disk_name = record.filename
    elif record.type == "glossary":
        download_name = f"{stem}.glossary.csv"
        disk_name = record.filename
    else:
        download_name = record.filename
        disk_name = record.filename

    path = app.state.storage["jobs"] / job.folder_name / disk_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="file missing on disk")

    file_size = path.stat().st_size
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename=\"{download_name}\"',
    }
    range_header = request.headers.get("range")
    if range_header:
        match = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if not match:
            return Response(status_code=416, headers=headers)
        start_str, end_str = match.groups()
        if start_str == "" and end_str == "":
            return Response(status_code=416, headers=headers)
        if start_str == "":
            length = int(end_str)
            start = max(file_size - length, 0)
            end = file_size - 1
        else:
            start = int(start_str)
            end = file_size - 1 if end_str == "" else min(int(end_str), file_size - 1)
        if start >= file_size:
            return Response(status_code=416, headers=headers)
        headers.update(
            {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(end - start + 1),
            }
        )
        media_type = (
            "text/csv" if record.type == "glossary" else "application/pdf"
        )
        return StreamingResponse(
            _iter_file_range(path, start, end),
            status_code=206,
            media_type=media_type,
            headers=headers,
        )

    headers["Content-Length"] = str(file_size)
    media_type = "text/csv" if record.type == "glossary" else "application/pdf"
    return StreamingResponse(
        _iter_file_range(path, 0, file_size - 1),
        media_type=media_type,
        headers=headers,
    )


@app.on_event("startup")
def _startup():
    app.state.storage = ensure_storage(app.state.settings)
    init_db(app.state.settings.db_path)
    queue_store.reset_running_to_queued(app.state.settings)
    queue_store.sync_queued_jobs(app.state.settings)
    snapshot = queue_store.snapshot(app.state.settings)
    SCHEDULER.configure(app.state.settings.max_running)
    SCHEDULER.load_queued(snapshot["queued"])

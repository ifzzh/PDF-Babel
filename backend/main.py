import json
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

from backend.config import settings
from backend.channels import get_channels
from backend.db import init_db
from backend.jobs import create_job
from backend.jobs import get_job_by_id
from backend.jobs import list_jobs
from backend.jobs import rename_job
from backend.files import create_file_record
from backend.files import get_file_by_id
from backend.files import list_files_by_job
from backend.storage import ensure_storage

app = FastAPI()
app.state.settings = settings


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/channels")
def channels():
    return get_channels()


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
    channels = get_channels()
    pool = channels.get(mode, [])
    channel = next((c for c in pool if c.get("id") == channel_id), None)
    if channel is None:
        raise HTTPException(status_code=400, detail="unsupported channel_id")
    if not channel.get("visible", True):
        raise HTTPException(status_code=400, detail="channel not visible")
    if not channel.get("enabled", True):
        raise HTTPException(status_code=400, detail="channel disabled")
    return channel


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
        "original_filename": record.original_filename,
    }


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
    return {
        "items": [
            {
                "job_id": job.id,
                "folder_name": job.folder_name,
                "created_at": job.created_at,
                "renamed_at": job.renamed_at,
                "status": job.status,
                "has_mono": False,
                "has_dual": False,
            }
            for job in items
        ],
        "total": total,
    }


@app.patch("/api/jobs/{job_id}")
def rename_job_endpoint(job_id: str, payload: dict):
    folder_name = payload.get("folder_name")
    original_filename = payload.get("original_filename")
    confirm = bool(payload.get("confirm", False))
    if folder_name is None and original_filename is None:
        raise HTTPException(status_code=400, detail="no changes provided")
    try:
        record, suggestions = rename_job(
            app.state.settings,
            app.state.storage["jobs"],
            job_id,
            folder_name,
            original_filename,
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
        return StreamingResponse(
            _iter_file_range(path, start, end),
            status_code=206,
            media_type="application/pdf",
            headers=headers,
        )

    headers["Content-Length"] = str(file_size)
    return StreamingResponse(
        _iter_file_range(path, 0, file_size - 1),
        media_type="application/pdf",
        headers=headers,
    )


@app.on_event("startup")
def _startup():
    app.state.storage = ensure_storage(app.state.settings)
    init_db(app.state.settings.db_path)

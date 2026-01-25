import json

from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile

from backend.config import settings
from backend.channels import get_channels
from backend.db import init_db
from backend.jobs import create_job
from backend.jobs import get_job_by_id
from backend.jobs import list_jobs
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
                "status": job.status,
                "has_mono": False,
                "has_dual": False,
            }
            for job in items
        ],
        "total": total,
    }


@app.on_event("startup")
def _startup():
    app.state.storage = ensure_storage(app.state.settings)
    init_db(app.state.settings.db_path)

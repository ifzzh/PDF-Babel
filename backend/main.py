from fastapi import FastAPI

from backend.config import settings
from backend.channels import get_channels
from backend.db import init_db
from backend.storage import ensure_storage

app = FastAPI()
app.state.settings = settings


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/channels")
def channels():
    return get_channels()


@app.on_event("startup")
def _startup():
    app.state.storage = ensure_storage(app.state.settings)
    init_db(app.state.settings.db_path)

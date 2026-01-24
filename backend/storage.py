import os
from pathlib import Path

from backend.config import Settings


def ensure_storage(settings: Settings) -> dict[str, Path]:
    root = settings.data_root
    jobs_dir = root / "jobs"
    db_dir = root / "db"
    for path in (root, jobs_dir, db_dir):
        path.mkdir(parents=True, exist_ok=True)
    if not os.access(root, os.W_OK):
        raise PermissionError(f"storage root not writable: {root}")
    return {"root": root, "jobs": jobs_dir, "db": db_dir}

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_root: Path
    db_path: Path
    log_level: str
    timezone: str
    max_running: int


def get_settings() -> Settings:
    data_root = Path(os.getenv("BABELDOC_DATA_ROOT", "/mnt/raid1/babeldoc-data"))
    db_path_env = os.getenv("BABELDOC_DB_PATH")
    if db_path_env:
        db_path = Path(db_path_env)
    else:
        db_path = data_root / "db" / "db.sqlite3"
    log_level = os.getenv("BABELDOC_LOG_LEVEL", "INFO")
    timezone = os.getenv("BABELDOC_TIMEZONE", "Asia/Shanghai")
    max_running_env = os.getenv("BABELDOC_MAX_RUNNING", "1")
    try:
        max_running = int(max_running_env)
    except ValueError:
        max_running = 1
    if max_running < 1:
        max_running = 1
    return Settings(
        data_root=data_root,
        db_path=db_path,
        log_level=log_level,
        timezone=timezone,
        max_running=max_running,
    )


settings = get_settings()

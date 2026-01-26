from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    data_root: Path
    db_path: Path
    log_level: str
    timezone: str
    max_running: int
    platform_config_path: Path
    platform_deepseek_base_url: str
    platform_deepseek_api_key: str
    platform_deepseek_model: str


def _load_platform_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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

    platform_config_path = Path(
        os.getenv(
            "BABELDOC_PLATFORM_CONFIG",
            str(data_root / "config" / "platform.json"),
        )
    )
    platform_config = _load_platform_config(platform_config_path)
    platform_section = platform_config.get("platform", {})
    deepseek_section = platform_section.get("deepseek", {})
    platform_deepseek_base_url = deepseek_section.get(
        "base_url", "https://api.deepseek.com/v1"
    )
    platform_deepseek_model = deepseek_section.get("model", "deepseek-chat")
    platform_deepseek_api_key = deepseek_section.get("api_key", "")

    env_base_url = os.getenv("BABELDOC_PLATFORM_DEEPSEEK_BASE_URL")
    if env_base_url:
        platform_deepseek_base_url = env_base_url
    env_api_key = os.getenv("BABELDOC_PLATFORM_DEEPSEEK_API_KEY")
    if env_api_key:
        platform_deepseek_api_key = env_api_key
    env_model = os.getenv("BABELDOC_PLATFORM_DEEPSEEK_MODEL")
    if env_model:
        platform_deepseek_model = env_model
    return Settings(
        data_root=data_root,
        db_path=db_path,
        log_level=log_level,
        timezone=timezone,
        max_running=max_running,
        platform_config_path=platform_config_path,
        platform_deepseek_base_url=platform_deepseek_base_url,
        platform_deepseek_api_key=platform_deepseek_api_key,
        platform_deepseek_model=platform_deepseek_model,
    )


settings = get_settings()

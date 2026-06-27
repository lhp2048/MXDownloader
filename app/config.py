import os
import shutil
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "family_mediacenter.db"
DOWNLOAD_DIR = PROJECT_ROOT / "downloads"


def default_download_dir() -> str:
    return str(DOWNLOAD_DIR.resolve())


DEFAULT_YTDLP_PATH = "yt-dlp"
VENV_YTDLP_PATH = PROJECT_ROOT / ".venv" / "bin" / "yt-dlp"


def resolve_ytdlp_executable(path_cfg: str | None = None) -> str:
    """Resolve yt-dlp binary; prefer project .venv when config uses default name."""
    raw = (path_cfg or DEFAULT_YTDLP_PATH).strip() or DEFAULT_YTDLP_PATH

    if raw != DEFAULT_YTDLP_PATH:
        p = Path(raw)
        if p.is_file():
            return str(p.resolve())
        found = shutil.which(raw)
        if found:
            return found
        return raw

    if VENV_YTDLP_PATH.is_file():
        return str(VENV_YTDLP_PATH.resolve())
    found = shutil.which(DEFAULT_YTDLP_PATH)
    return found or raw


def resolve_download_dir(path: str | None = None) -> str:
    """Resolve download path; relative paths are under project root."""
    target = Path(path or default_download_dir())
    if not target.is_absolute():
        target = PROJECT_ROOT / target
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


class Aria2Settings(BaseSettings):
    rpc_url: str = "http://127.0.0.1:6800/jsonrpc"
    secret: str = ""


class AlistSettings(BaseSettings):
    enabled: bool = False
    url: str = "http://127.0.0.1:5244"
    token: str = ""


class EngineSettings(BaseSettings):
    ytdlp_path: str = "yt-dlp"
    aria2: Aria2Settings = Field(default_factory=Aria2Settings)
    alist: AlistSettings = Field(default_factory=AlistSettings)


class DownloadSettings(BaseSettings):
    default_dir: str = Field(default_factory=default_download_dir)
    max_concurrent: int = 3


class ServerSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 18026
    api_key: str = ""


class FilesSettings(BaseSettings):
    public_access: bool = True
    public_base_url: str = ""


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FAMILY_MEDIACENTER_", extra="ignore")

    server: ServerSettings = Field(default_factory=ServerSettings)
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    engines: EngineSettings = Field(default_factory=EngineSettings)
    files: FilesSettings = Field(default_factory=FilesSettings)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_settings() -> AppSettings:
    data: dict[str, Any] = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded

    env_url = os.environ.get("FAMILY_MEDIACENTER_URL")
    if env_url:
        # FAMILY_MEDIACENTER_URL used by MCP; host/port can still override via env
        pass

    s = AppSettings(**data)
    s.download.default_dir = resolve_download_dir(s.download.default_dir)
    return s


def save_settings(settings: AppSettings) -> None:
    data = {
        "server": settings.server.model_dump(),
        "download": settings.download.model_dump(),
        "files": settings.files.model_dump(),
        "engines": {
            "ytdlp_path": settings.engines.ytdlp_path,
            "aria2": settings.engines.aria2.model_dump(),
            "alist": settings.engines.alist.model_dump(),
        },
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)


settings = load_settings()

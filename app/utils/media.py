from pathlib import Path
from typing import Optional

from app.services.file_manager import get_download_root, resolve_safe_path

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".m4v"}
AUDIO_EXT = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".opus"}
MEDIA_EXT = VIDEO_EXT | AUDIO_EXT


def media_type_for_path(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    return ""


def is_media_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() in MEDIA_EXT


def to_rel_path(abs_path: str | Path) -> str:
    root = get_download_root().resolve()
    target = Path(abs_path).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return ""


def resolve_media_rel_path(rel_path: str) -> Path:
    return resolve_safe_path(rel_path)


def media_display_name(rel_path: str, title: str = "") -> str:
    if title:
        return title
    return Path(rel_path).name

import re
from typing import Optional
from urllib.parse import urlparse

from app.models.task import SourceType


YTDLP_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "bilibili.com",
    "b23.tv",
    "douyin.com",
    "iesdouyin.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "vimeo.com",
    "dailymotion.com",
    "nicovideo.jp",
    "twitch.tv",
)


def detect_engine(url: str, forced: Optional[str] = None) -> str:
    if forced:
        return forced.lower()

    lower = url.lower().strip()
    if lower.startswith("alist://"):
        return SourceType.ALIST.value
    if lower.startswith("magnet:"):
        return SourceType.ARIA2.value
    if lower.endswith(".torrent"):
        return SourceType.ARIA2.value

    parsed = urlparse(lower)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if "/s/" in path or "alist" in host:
        return SourceType.ALIST.value

    for domain in YTDLP_DOMAINS:
        if domain in host:
            return SourceType.YTDLP.value

    if parsed.scheme in ("http", "https", "ftp"):
        return SourceType.ARIA2.value

    return SourceType.ARIA2.value

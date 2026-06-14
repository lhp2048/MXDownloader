import re
from typing import Optional

# 从分享文案中提取 URL（抖音/B站等常带前后说明文字）
_URL_RE = re.compile(
    r"(magnet:[^\s<>'\"，。！？；、）】》]+"
    r"|alist://[^\s<>'\"，。！？；、）】》]+"
    r"|https?://[^\s<>'\"，。！？；、）】》]+"
    r"|ftp://[^\s<>'\"，。！？；、）】》]+)",
    re.IGNORECASE,
)

_VIDEO_HINTS = (
    "douyin.com",
    "iesdouyin.com",
    "bilibili.com",
    "b23.tv",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "vimeo.com",
    "twitch.tv",
)

_TRAILING = ".,;:!?)]}»\"'，。！？；、）】》』"


def _clean_url(url: str) -> str:
    return url.strip().rstrip(_TRAILING)


def _is_plain_url(text: str) -> bool:
    t = text.strip()
    return t.startswith(("http://", "https://", "magnet:", "alist://", "ftp://"))


def extract_url_from_text(text: str) -> str:
    """
    从分享文案中提取第一个可用链接；若含多个链接，优先音视频站点。
    若本身已是纯 URL，原样返回。
    """
    raw = (text or "").strip()
    if not raw:
        return raw

    if _is_plain_url(raw) and not re.search(r"\s", raw):
        return raw.strip()

    matches = [_clean_url(m) for m in _URL_RE.findall(raw)]
    if not matches:
        return raw

    for url in matches:
        lower = url.lower()
        for hint in _VIDEO_HINTS:
            if hint in lower:
                return url

    return matches[0]


def extract_all_urls_from_text(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    if _is_plain_url(raw) and not re.search(r"\s", raw):
        return [raw.strip()]
    return [_clean_url(m) for m in _URL_RE.findall(raw)]

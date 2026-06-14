import locale
import os
import sys


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        env.setdefault("PYTHONLEGACYWINDOWSSTDIO", "0")
    return env


def decode_bytes(data: bytes) -> str:
    if not data:
        return ""
    if sys.platform == "win32":
        encodings = ["gbk", "cp936", locale.getpreferredencoding(False), "utf-8"]
    else:
        encodings = ["utf-8", locale.getpreferredencoding(False)]
    seen: set[str] = set()
    for enc in encodings:
        if not enc:
            continue
        key = enc.lower().replace("-", "")
        if key in seen:
            continue
        seen.add(key)
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def title_from_task_file(file_path: str, task_id: int) -> str:
    from pathlib import Path

    stem = Path(file_path).stem
    prefix = f"task_{task_id}_"
    if stem.startswith(prefix):
        return stem[len(prefix):]
    return stem

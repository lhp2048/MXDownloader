import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx

from app.config import load_settings, resolve_download_dir
from app.utils.encoding import decode_bytes, subprocess_env


@dataclass
class EngineStatusInfo:
    name: str
    display_name: str
    description: str
    available: bool
    enabled: bool
    version: str = ""
    endpoint: str = ""
    message: str = ""
    supports: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    active_tasks: int = 0


async def _run_version_cmd(cmd: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=subprocess_env(),
    )
    stdout, _ = await proc.communicate()
    text = decode_bytes(stdout).strip()
    if proc.returncode != 0:
        raise RuntimeError(text or f"exit code {proc.returncode}")
    return text.split("\n")[0].strip()


async def get_ytdlp_status(settings=None) -> EngineStatusInfo:
    s = settings or load_settings()
    path_cfg = s.engines.ytdlp_path
    resolved = shutil.which(path_cfg)
    if not resolved and Path(path_cfg).exists():
        resolved = str(Path(path_cfg).resolve())

    info = EngineStatusInfo(
        name="ytdlp",
        display_name="yt-dlp",
        description="音视频下载（YouTube、Bilibili、Twitter 等）",
        available=False,
        enabled=True,
        endpoint=resolved or path_cfg,
        supports=["音视频站点", "播客", "直播回放"],
        config={"ytdlp_path": path_cfg},
    )

    if not resolved:
        info.message = "未找到 yt-dlp，请安装或配置正确路径"
        return info

    try:
        info.version = await _run_version_cmd([resolved, "--version"])
        info.available = True
        info.message = "运行正常"
    except Exception as e:
        info.message = str(e)

    return info


async def get_aria2_status(settings=None) -> EngineStatusInfo:
    s = settings or load_settings()
    aria_cfg = s.engines.aria2
    info = EngineStatusInfo(
        name="aria2",
        display_name="aria2",
        description="HTTP/HTTPS 直链、磁力链接、BT 下载",
        available=False,
        enabled=True,
        endpoint=aria_cfg.rpc_url,
        supports=["HTTP/HTTPS", "磁力链接", "BT"],
        config={
            "rpc_url": aria_cfg.rpc_url,
            "secret": "***" if aria_cfg.secret else "",
        },
    )

    try:
        from app.engines.aria2 import Aria2Engine

        engine = Aria2Engine()
        client = engine._client()
        version = client.client.get_version()
        info.version = str(version.get("version", version) if isinstance(version, dict) else version)
        downloads = client.get_downloads()
        info.active_tasks = sum(1 for d in downloads if d.is_active)
        info.available = True
        info.message = f"RPC 连接正常，活跃任务 {info.active_tasks} 个"
    except Exception as e:
        info.message = f"无法连接 aria2 RPC: {e}"

    return info


async def get_alist_status(settings=None) -> EngineStatusInfo:
    s = settings or load_settings()
    alist_cfg = s.engines.alist
    info = EngineStatusInfo(
        name="alist",
        display_name="Alist / OpenList",
        description="网盘统一接入、分享链接解析与离线下载",
        available=False,
        enabled=alist_cfg.enabled,
        endpoint=alist_cfg.url,
        supports=["网盘分享链接", "Alist 路径", "离线下载到网盘"],
        config={
            "enabled": alist_cfg.enabled,
            "url": alist_cfg.url,
            "token": "***" if alist_cfg.token else "",
        },
    )

    if not alist_cfg.enabled:
        info.message = "未启用，请在设置中开启"
        return info

    if not alist_cfg.url:
        info.message = "未配置服务地址"
        return info

    try:
        base = alist_cfg.url.rstrip("/")
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{base}/api/public/settings")
            r.raise_for_status()
            body = r.json()
            if body.get("code") == 200:
                data = body.get("data", {})
                info.version = str(data.get("version", ""))
                info.available = True
                info.message = "服务连接正常"
            else:
                info.message = body.get("message", "Alist API 返回异常")
    except Exception as e:
        info.message = f"无法连接 Alist: {e}"

    return info


async def get_all_engine_status() -> list[EngineStatusInfo]:
    s = load_settings()
    results = await asyncio.gather(
        get_ytdlp_status(s),
        get_aria2_status(s),
        get_alist_status(s),
    )
    return list(results)


async def get_engine_status(name: str) -> Optional[EngineStatusInfo]:
    mapping = {
        "ytdlp": get_ytdlp_status,
        "aria2": get_aria2_status,
        "alist": get_alist_status,
    }
    fn = mapping.get(name.lower())
    if not fn:
        return None
    return await fn()


def status_to_dict(info: EngineStatusInfo) -> dict[str, Any]:
    return {
        "name": info.name,
        "display_name": info.display_name,
        "description": info.description,
        "available": info.available,
        "enabled": info.enabled,
        "version": info.version,
        "endpoint": info.endpoint,
        "message": info.message,
        "supports": info.supports,
        "config": info.config,
        "active_tasks": info.active_tasks,
    }


async def get_system_summary() -> dict[str, Any]:
    s = load_settings()
    engines = await get_all_engine_status()
    return {
        "download_dir": resolve_download_dir(s.download.default_dir),
        "max_concurrent": s.download.max_concurrent,
        "server_url": f"http://{s.server.host}:{s.server.port}",
        "engines_total": len(engines),
        "engines_available": sum(1 for e in engines if e.available),
        "engines": [status_to_dict(e) for e in engines],
    }

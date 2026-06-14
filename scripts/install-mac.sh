#!/usr/bin/env bash
# MyDownloader macOS 环境安装（开发 / 生产首次部署）
# 用法: ./scripts/install-mac.sh [--with-docker] [--skip-brew]

set -euo pipefail

WITH_DOCKER=0
SKIP_BREW=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-docker)
            WITH_DOCKER=1
            shift
            ;;
        --skip-brew)
            SKIP_BREW=1
            shift
            ;;
        -h|--help)
            echo "用法: $0 [--with-docker] [--skip-brew]"
            echo "  --with-docker  安装后启动 docker-compose（aria2 + Alist）"
            echo "  --skip-brew    不通过 Homebrew 安装 yt-dlp / aria2"
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[install-mac] $*"; }

if ! command -v python3 >/dev/null 2>&1; then
    log "未找到 python3。请先安装 Python 3.10+："
    log "  brew install python@3.12"
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
log "Python $PY_VER"

if [[ "$SKIP_BREW" -eq 0 ]] && command -v brew >/dev/null 2>&1; then
    log "通过 Homebrew 安装 yt-dlp、aria2（已安装则跳过）..."
    brew install yt-dlp aria2 || true
elif [[ "$SKIP_BREW" -eq 0 ]]; then
    log "未检测到 Homebrew，跳过 brew 安装。可手动: brew install yt-dlp aria2"
fi

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    log "创建虚拟环境 .venv ..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

# shellcheck disable=SC1091
source "$PROJECT_ROOT/.venv/bin/activate"

log "安装 Python 依赖..."
pip install -U pip setuptools wheel
pip install -e .
pip install yt-dlp

mkdir -p "$PROJECT_ROOT/downloads" "$PROJECT_ROOT/logs" "$PROJECT_ROOT/data"

chmod +x "$PROJECT_ROOT/scripts/start.sh" "$PROJECT_ROOT/start.command" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/install-mac.sh" 2>/dev/null || true

log "检测组件..."
python3 - <<'PY'
import asyncio
from app.services.engine_status import get_ytdlp_status, get_aria2_status, get_alist_status

async def main():
    for coro in (get_ytdlp_status(), get_aria2_status(), get_alist_status()):
        info = await coro
        mark = "OK" if info.available else "MISS"
        print(f"  [{mark}] {info.display_name}: {info.message}")

asyncio.run(main())
PY

if [[ "$WITH_DOCKER" -eq 1 ]]; then
    if ! command -v docker >/dev/null 2>&1; then
        log "未找到 Docker。请先安装 Docker Desktop for Mac。"
        exit 1
    fi
    log "启动 docker-compose（aria2 + Alist）..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
    log "请在 config.yaml 中配置 aria2.secret=mydownloader 并启用 alist"
fi

log "========================================"
log "安装完成。"
log "启动: ./scripts/start.sh  或双击 start.command"
log "生产常驻: 见 docs/DEPLOY_MAC.md（launchd）"
log "========================================"

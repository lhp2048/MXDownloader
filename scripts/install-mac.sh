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
            echo "  --skip-brew    不通过 Homebrew 安装 python / yt-dlp / aria2"
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

# shellcheck source=lib/python.sh
source "$SCRIPT_DIR/lib/python.sh"

log() { echo "[install-mac] $*"; }

_get_macos_major() {
    sw_vers -productVersion 2>/dev/null | cut -d. -f1 || true
}

MACOS_MAJOR=""

if [[ "$SKIP_BREW" -eq 0 ]] && command -v brew >/dev/null 2>&1; then
    MACOS_MAJOR="$(_get_macos_major)"
    if [[ -z "${MACOS_MAJOR}" ]] || [[ "${MACOS_MAJOR}" -ge 13 ]]; then
        if ! resolve_project_python "$PROJECT_ROOT"; then
            log "未找到 Python 3.10+，尝试 brew install python@3.12 ..."
            try_brew_install_python || true
        fi
    else
        log "macOS ${MACOS_MAJOR}：跳过 brew 安装 Python（Monterey 等旧系统请用 python.org 安装包）"
        log "  https://www.python.org/downloads/macos/"
    fi
    log "尝试 Homebrew 安装 aria2（可选，失败可改用 Docker）..."
    brew install aria2 2>/dev/null || log "aria2 brew 安装未成功，可用: docker compose up -d aria2"
    log "yt-dlp 将通过 pip 安装（macOS 12 上勿用 brew install yt-dlp）"
fi

if ! resolve_project_python "$PROJECT_ROOT"; then
    print_python_install_help "[install-mac] "
    exit 1
fi

PYTHON_BIN="$RESOLVED_PYTHON_BIN"
log "选用 Python $RESOLVED_PYTHON_VER ($PYTHON_BIN)"

if [[ -d "$PROJECT_ROOT/.venv" ]] && ! venv_python_ok "$PROJECT_ROOT"; then
    VENV_VER="$(_python_version_string "$PROJECT_ROOT/.venv/bin/python" 2>/dev/null || echo '?')"
    log "现有 .venv 为 Python $VENV_VER（< 3.10），将自动重建..."
    rm -rf "$PROJECT_ROOT/.venv"
fi

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    log "创建虚拟环境 .venv ..."
    "$PYTHON_BIN" -m venv "$PROJECT_ROOT/.venv"
fi

# shellcheck disable=SC1091
source "$PROJECT_ROOT/.venv/bin/activate"

log "venv Python: $(python -c 'import sys; print(sys.version.split()[0])') ($(command -v python))"

log "安装 Python 依赖..."
pip install -U pip setuptools wheel
pip install -e .
pip install yt-dlp

YTDLP_VENV="$PROJECT_ROOT/.venv/bin/yt-dlp"
if [[ -x "$YTDLP_VENV" ]]; then
    log "yt-dlp 已安装: $YTDLP_VENV"
    log "若设置页检测不到，将 ytdlp_path 设为: $YTDLP_VENV"
fi

mkdir -p "$PROJECT_ROOT/downloads" "$PROJECT_ROOT/logs" "$PROJECT_ROOT/data"

chmod +x "$PROJECT_ROOT/scripts/lib/python.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/start.sh" "$PROJECT_ROOT/start.command" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/install-mac.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/install-launchd.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/restart.sh" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/restart.command" 2>/dev/null || true
chmod +x "$PROJECT_ROOT/install-launchd.command" 2>/dev/null || true

log "检测组件..."
python - <<'PY'
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
log "开机自启: ./scripts/install-launchd.sh  或双击 install-launchd.command"
log "重启服务: ./scripts/restart.sh  或双击 restart.command"
log "详见: docs/DEPLOY_MAC.md"
log "========================================"

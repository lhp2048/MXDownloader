#!/usr/bin/env bash
# 安装 / 卸载 MXDownloader launchd 开机自启服务（macOS）
# 用法:
#   ./scripts/install-launchd.sh          # 安装并启动
#   ./scripts/install-launchd.sh --uninstall

set -euo pipefail

UNINSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        -h|--help)
            echo "用法: $0 [--uninstall]"
            echo "  安装 launchd 用户服务：登录后自动启动，崩溃自动拉起"
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
LABEL="com.mydownloader.service"
PLIST_NAME="${LABEL}.plist"
PLIST_SRC="$PROJECT_ROOT/deploy/mydownloader.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
UID_NUM="$(id -u)"
DOMAIN="gui/$UID_NUM"

log() { echo "[install-launchd] $*"; }

unload_service() {
    if [[ -f "$PLIST_DST" ]]; then
        launchctl bootout "$DOMAIN" "$PLIST_DST" 2>/dev/null || \
            launchctl unload "$PLIST_DST" 2>/dev/null || true
    fi
}

if [[ "$UNINSTALL" -eq 1 ]]; then
    log "卸载 launchd 服务..."
    unload_service
    if [[ -f "$PLIST_DST" ]]; then
        rm -f "$PLIST_DST"
        log "已删除 $PLIST_DST"
    fi
    log "卸载完成。"
    exit 0
fi

if [[ ! -f "$PLIST_SRC" ]]; then
    log "未找到模板: $PLIST_SRC"
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    log "未找到虚拟环境 Python: $PYTHON_BIN"
    log "请先执行: ./scripts/install-mac.sh"
    exit 1
fi

mkdir -p "$PROJECT_ROOT/logs" "$HOME/Library/LaunchAgents"

log "项目目录: $PROJECT_ROOT"
log "生成 plist: $PLIST_DST"

sed "s|__PROJECT_ROOT__|${PROJECT_ROOT}|g" "$PLIST_SRC" > "$PLIST_DST"

unload_service

if launchctl bootstrap "$DOMAIN" "$PLIST_DST" 2>/dev/null; then
    log "已通过 launchctl bootstrap 加载服务"
else
    log "bootstrap 失败，尝试 launchctl load ..."
    launchctl load "$PLIST_DST"
fi

launchctl enable "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl kickstart -k "$DOMAIN/$LABEL" 2>/dev/null || launchctl start "$LABEL" 2>/dev/null || true

log "========================================"
log "开机自启服务已安装"
log "  标签: $LABEL"
log "  日志: $PROJECT_ROOT/logs/launchd.out.log"
log "  错误: $PROJECT_ROOT/logs/launchd.err.log"
log "  重启: ./scripts/restart.sh"
log "  卸载: ./scripts/install-launchd.sh --uninstall"
log "========================================"

sleep 1
if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
    log "服务状态: 已注册"
else
    log "警告: 无法确认服务状态，请查看日志"
fi

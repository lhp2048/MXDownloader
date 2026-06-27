#!/usr/bin/env bash
# 重启 Family Media Center 服务（macOS / Linux）
# 若已安装 launchd 服务则 kickstart；否则结束占用端口并后台启动

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# shellcheck source=lib/python.sh
source "$SCRIPT_DIR/lib/python.sh"

LABEL="com.family.mediacenter.service"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
UID_NUM="$(id -u)"
DOMAIN="gui/$UID_NUM"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/family_mediacenter-$(date +%Y%m%d).log"

log() {
    local line="[$(date '+%Y-%m-%d %H:%M:%S')] [restart] $*"
    echo "$line"
    echo "$line" >> "$LOG_FILE"
}

get_port() {
    local py_bin
    if resolve_project_python "$PROJECT_ROOT"; then
        py_bin="$RESOLVED_PYTHON_BIN"
    elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
        py_bin="$PROJECT_ROOT/.venv/bin/python"
    else
        echo "18026"
        return
    fi
    "$py_bin" -c \
        "from app.config import load_settings; print(load_settings().server.port)" \
        2>/dev/null || echo "18026"
}

stop_port_listener() {
    local port="$1"
    local pids
    pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
        log "停止占用端口 $port 的进程: PID $pids"
        # shellcheck disable=SC2086
        kill $pids 2>/dev/null || true
        sleep 1
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
    fi
}

start_background() {
    local port host python_bin
    port="$(get_port)"

    if ! resolve_project_python "$PROJECT_ROOT"; then
        log "未找到 Python 3.10+，请先 ./scripts/install-mac.sh"
        print_python_install_help "[restart] "
        exit 1
    fi
    python_bin="$RESOLVED_PYTHON_BIN"
    log "使用 Python $RESOLVED_PYTHON_VER ($python_bin)"

    host="$("$python_bin" -c "from app.config import load_settings; print(load_settings().server.host)" 2>/dev/null || echo "127.0.0.1")"

    stop_port_listener "$port"

    log "后台启动服务 (port $port)..."
    export PYTHONUNBUFFERED=1
    export PYTHONUTF8=1
    nohup "$python_bin" -u -m app.main >> "$LOG_FILE" 2>&1 &
    disown 2>/dev/null || true
    sleep 1

    if lsof -ti tcp:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        log "服务已启动: http://${host}:${port}"
        log "日志: $LOG_FILE"
    else
        log "启动可能失败，请查看: $LOG_FILE"
        exit 1
    fi
}

restart_launchd() {
    log "通过 launchd 重启服务 ($LABEL)..."
    if launchctl kickstart -k "$DOMAIN/$LABEL" 2>/dev/null; then
        log "launchd 重启完成"
        return 0
    fi
    if launchctl kickstart -k "$LABEL" 2>/dev/null; then
        log "launchd 重启完成"
        return 0
    fi
    log "kickstart 失败，尝试 load + start ..."
    launchctl bootstrap "$DOMAIN" "$PLIST_DST" 2>/dev/null || launchctl load "$PLIST_DST" 2>/dev/null || true
    launchctl kickstart -k "$DOMAIN/$LABEL" 2>/dev/null || launchctl start "$LABEL" 2>/dev/null || true
}

if [[ -f "$PLIST_DST" ]] && launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
    restart_launchd
else
    log "未检测到 launchd 服务，使用端口方式重启"
    log "安装开机自启: ./scripts/install-launchd.sh"
    start_background
fi

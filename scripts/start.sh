#!/usr/bin/env bash
# MyDownloader 启动脚本（macOS / Linux，控制台 + 日志文件）

set -euo pipefail

NO_KILL=0

usage() {
    echo "用法: $0 [--no-kill]"
    echo "  --no-kill  端口被占用时不自动结束旧进程"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-kill)
            NO_KILL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            usage
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# shellcheck source=lib/python.sh
source "$SCRIPT_DIR/lib/python.sh"

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/mydownloader-$(date +%Y%m%d).log"

write_log() {
    local message="$1"
    local line="[$(date '+%Y-%m-%d %H:%M:%S')] $message"
    echo "$line"
    echo "$line" >> "$LOG_FILE"
}

get_config_value() {
    local expr="$1"
    local default="$2"
    "$PYTHON_BIN" -c "$expr" 2>/dev/null || echo "$default"
}

if ! resolve_project_python "$PROJECT_ROOT"; then
    write_log "未找到 Python 3.10+，请先运行: ./scripts/install-mac.sh"
    print_python_install_help "[start] "
    exit 1
fi

PYTHON_BIN="$RESOLVED_PYTHON_BIN"

PORT="$(get_config_value "from app.config import load_settings; print(load_settings().server.port)" "18026")"
HOST="$(get_config_value "from app.config import load_settings; print(load_settings().server.host)" "127.0.0.1")"

write_log "========================================"
write_log "MyDownloader 启动"
write_log "项目目录: $PROJECT_ROOT"
write_log "日志文件: $LOG_FILE"
write_log "Python $RESOLVED_PYTHON_VER: $PYTHON_BIN"

stop_listener_on_port() {
    local port="$1"
    local pids
    pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
        write_log "停止占用端口 $port 的进程: PID $pids"
        # shellcheck disable=SC2086
        kill $pids 2>/dev/null || true
        sleep 1
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
    fi
}

if [[ "$NO_KILL" -eq 0 ]]; then
    stop_listener_on_port "$PORT"
fi

write_log "服务地址: http://${HOST}:${PORT}"
write_log "按 Ctrl+C 停止服务"
write_log "========================================"

export PYTHONUNBUFFERED=1

# tee 同步输出到控制台与日志文件
"$PYTHON_BIN" -u -m app.main 2>&1 | tee -a "$LOG_FILE"

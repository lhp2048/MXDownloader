#!/usr/bin/env bash
# 在 macOS / Linux 上解析 Python 3.10+ 可执行文件
# 用法: source "$(dirname "$0")/lib/python.sh"

PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=10

RESOLVED_PYTHON_BIN=""
RESOLVED_PYTHON_VER=""

_python_version_ok() {
    local bin="$1"
    [[ -n "$bin" && -x "$bin" ]] || return 1
    "$bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null
}

_python_version_string() {
    local bin="$1"
    "$bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "?"
}

# 收集候选路径（优先级从高到低），去重后返回第一个满足 3.10+ 的
resolve_project_python() {
    local project_root="${1:-}"
    local candidates=()
    local seen="|"
    local bin ver base

    if [[ -n "$project_root" && -x "$project_root/.venv/bin/python" ]]; then
        candidates+=("$project_root/.venv/bin/python")
    fi

  for base in /opt/homebrew/bin /usr/local/bin; do
        for ver in python3.13 python3.12 python3.11 python3.10; do
            candidates+=("$base/$ver")
        done
    done

    for ver in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$ver" >/dev/null 2>&1; then
            candidates+=("$(command -v "$ver")")
        fi
    done

    RESOLVED_PYTHON_BIN=""
    RESOLVED_PYTHON_VER=""

    for bin in "${candidates[@]}"; do
        [[ -n "$bin" ]] || continue
        case "$seen" in *"|${bin}|"*) continue ;; esac
        seen="${seen}${bin}|"
        if _python_version_ok "$bin"; then
            RESOLVED_PYTHON_BIN="$bin"
            RESOLVED_PYTHON_VER="$(_python_version_string "$bin")"
            return 0
        fi
    done

    return 1
}

venv_python_ok() {
    local project_root="$1"
    local venv_py="$project_root/.venv/bin/python"
    [[ -x "$venv_py" ]] && _python_version_ok "$venv_py"
}

print_python_install_help() {
    local prefix="${1:-}"
    local sys_ver
    sys_ver="$(python3 --version 2>/dev/null || echo '未安装')"
    echo "${prefix}需要 Python >= 3.10，当前默认 python3: ${sys_ver}"
    echo "${prefix}macOS 自带 Python 3.9 无法使用。"
    echo "${prefix}安装: brew install python@3.12"
    echo "${prefix}然后: rm -rf .venv && ./scripts/install-mac.sh"
}

try_brew_install_python() {
    if ! command -v brew >/dev/null 2>&1; then
        return 1
    fi
    brew install python@3.12 || true
    return 0
}

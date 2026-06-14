#!/bin/bash
# macOS 双击：安装开机自启服务（需已执行 install-mac.sh）
cd "$(dirname "$0")"
exec bash "./scripts/install-launchd.sh"

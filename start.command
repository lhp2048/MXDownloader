#!/bin/bash
# macOS 双击启动：在 Terminal 中运行 MyDownloader
cd "$(dirname "$0")"
exec bash "./scripts/start.sh"

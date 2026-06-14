# MXDownloader

本地统一下载与媒体管理服务：集成 **yt-dlp**（音视频）、**aria2**（HTTP/磁力/BT）、**Alist**（网盘），提供 Web 后台、文件管理、多媒体播放列表，以及 WorkBuddy Skill / MCP 集成。

> 仓库名 **MXDownloader**，Python 包名仍为 `mydownloader`。

## 功能概览

| 模块 | 说明 |
|------|------|
| **下载引擎** | yt-dlp、aria2、Alist 可插拔，自动路由站点 |
| **Web 仪表盘** | 粘贴链接或分享文案、任务 Tab、实时进度 |
| **组件状态** | 引擎可用性检测与健康检查 |
| **文件管理** | 浏览 `downloads/`，外链 `/files/…`，删除与复制链接 |
| **多媒体中心** | 播放列表；默认列表自动收录完成的视频/音频 |
| **设置** | 分类折叠配置，含 yt-dlp / aria2 / Alist **安装帮助** |
| **REST API** | OpenAPI：`/docs` |
| **AI 集成** | WorkBuddy Skill + Cursor MCP |

## 环境要求

- Python **3.10+**
- 可选：Docker（aria2 + Alist）、Homebrew（macOS 安装引擎）

## 快速开始

### 1. 克隆与安装

```bash
git clone git@github.com:lhp2048/MXDownloader.git
cd MXDownloader
pip install -e .
pip install yt-dlp
```

### 2. 安装下载组件（可选）

| 组件 | 安装方式 |
|------|----------|
| yt-dlp | `pip install yt-dlp` 或 `brew install yt-dlp` |
| aria2 | `brew install aria2` / Scoop / **Docker**（推荐） |
| Alist | **Docker**（`docker compose up -d alist`） |

**macOS 一键**：`chmod +x scripts/install-mac.sh && ./scripts/install-mac.sh`

设置页展开各引擎条目可查看分平台安装命令。生产部署见 [docs/DEPLOY_MAC.md](docs/DEPLOY_MAC.md)。

### 3. 配置

编辑 `config.yaml`（节选）：

```yaml
server:
  host: 127.0.0.1   # 局域网访问改为 0.0.0.0
  port: 8766
  api_key: ""       # 生产环境建议设置

download:
  default_dir: downloads
  max_concurrent: 3

files:
  public_access: true
  public_base_url: ""

engines:
  ytdlp_path: yt-dlp
  aria2:
    rpc_url: http://127.0.0.1:6800/jsonrpc
    secret: mydownloader   # 与 docker-compose 中 RPC_SECRET 一致
  alist:
    enabled: false
    url: http://127.0.0.1:5244
    token: ""
```

### 4. 启动

| 平台 | 命令 |
|------|------|
| Windows | 双击 `start.bat` 或 `.\scripts\start.ps1` |
| macOS | 双击 `start.command` 或 `./scripts/start.sh` |
| 通用 | `python -m app.main` 或 `mydownloader` |

访问：**http://127.0.0.1:8766**

### 5. Docker（aria2 + Alist）

```bash
docker compose up -d
```

- aria2 RPC：`http://127.0.0.1:6800`，Secret：`mydownloader`
- Alist：http://127.0.0.1:5244（首次登录查看容器日志获取密码）

## Web 页面

| 路径 | 功能 |
|------|------|
| `/` | 下载任务仪表盘 |
| `/files` | 下载文件管理 |
| `/media` | 多媒体播放列表 |
| `/components` | 引擎组件状态 |
| `/settings` | 系统设置与安装帮助 |
| `/docs` | API 文档 |

## API 示例

```bash
# 创建下载（支持整段分享文案，自动提取 URL）
curl -X POST http://127.0.0.1:8766/api/v1/downloads \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bilibili.com/video/BV1xx"}'

# 任务列表
curl http://127.0.0.1:8766/api/v1/tasks?tab=completed

# 默认播放列表（轮播，免 API Key）
curl http://127.0.0.1:8766/api/v1/playlists/default/items

# 文件外链
curl -O http://127.0.0.1:8766/files/your-video.mp4

# 健康检查
curl http://127.0.0.1:8766/health
```

配置了 `api_key` 时，写操作需请求头：`X-API-Key: <your-key>`

完整 API 见 `skills/mydownloader/references/api.md`。

## WorkBuddy Skill

```bash
mkdir -p ~/.workbuddy/skills
cp -r skills/mydownloader ~/.workbuddy/skills/mydownloader
```

支持下载任务与**播放列表管理**（见 `skills/mydownloader/SKILL.md`）。

## Cursor MCP

```json
{
  "mcpServers": {
    "mydownloader": {
      "command": "python",
      "args": ["/path/to/MXDownloader/mcp_server/server.py"],
      "env": {
        "MYDOWNLOADER_URL": "http://127.0.0.1:8766",
        "MYDOWNLOADER_API_KEY": ""
      }
    }
  }
}
```

下载工具：`create_download`、`list_tasks`、`get_task`、`cancel_task` …

播放列表：`list_playlists`、`list_playlist_items`、`create_playlist`、`add_playlist_item` …

## 项目结构

```
MXDownloader/
├── app/                 # FastAPI 应用
│   ├── engines/         # yt-dlp, aria2, alist
│   ├── services/        # 任务、文件、播放列表
│   ├── api/             # REST + Web 路由
│   └── web/             # 模板与静态资源
├── skills/mydownloader/ # WorkBuddy Skill
├── mcp_server/          # MCP Server
├── scripts/             # 启动与 macOS 安装脚本
├── deploy/              # launchd 模板（macOS）
├── docs/DEPLOY_MAC.md   # macOS 生产部署
├── config.yaml
└── docker-compose.yml
```

## 许可证

MIT

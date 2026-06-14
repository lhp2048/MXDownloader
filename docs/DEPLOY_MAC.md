# macOS 生产环境部署指南

本文说明在 **Mac（Apple Silicon / Intel）** 上部署 MyDownloader 的完整流程：应用本身、下载组件、Docker 可选服务、以及 **launchd 常驻**。

## 支持情况概览

| 项目 | macOS 支持 | 说明 |
|------|------------|------|
| MyDownloader 主服务 | ✅ | Python 跨平台；已有 `start.command`、`scripts/start.sh` |
| yt-dlp | ✅ | `pip` 或 `brew install yt-dlp` |
| aria2 | ✅ | `brew install aria2` 或 Docker（推荐生产） |
| Alist | ✅ | 仅通过 Docker（`docker-compose.yml`） |
| 文件外链 `/files/` | ✅ | 与平台无关 |
| 编码 / 中文文件名 | ✅ | Unix 默认 UTF-8，无 Windows GBK 问题 |
| launchd 常驻 | ✅ | 模板见 `deploy/mydownloader.plist` |

### 关于「自动部署」

当前**没有**一键安装所有组件的 GUI 安装器，但提供：

1. **`scripts/install-mac.sh`** — 自动创建 venv、安装 Python 包、可选 `brew` 安装 yt-dlp/aria2、可选 `docker compose up`
2. **`docker-compose.yml`** — 一键拉起 aria2 + Alist（需已安装 Docker Desktop）
3. **组件页 `/components`** — 启动后检测各引擎是否可用（不自动安装，只诊断）

**不会自动完成的事项**（需手动或脚本外配置）：

- 安装 Python / Homebrew / Docker Desktop（Mac 上无这些则脚本会提示）
- Alist 首次登录改密码、获取 Token
- 反向代理、HTTPS、防火墙规则
- `config.yaml` 中 `server.host`、`files.public_base_url` 等生产参数

---

## 一、环境要求

- macOS 12+（Monterey 或更高推荐）
- **Python 3.10+**（`python3 --version`）— **系统自带的 3.9.x 不可用**
- 磁盘：下载目录预留足够空间（默认 `项目/downloads`）
- 可选：**Homebrew**、**Docker Desktop**

> **常见情况**：Mac 自带 `python3` 为 3.9.6，需用 Homebrew 安装新版：
> `brew install python@3.12`，然后重新运行 `./scripts/install-mac.sh`。

---

## 二、快速安装（推荐）

```bash
cd /path/to/MyDownloader
chmod +x scripts/install-mac.sh scripts/start.sh start.command

# 基础安装：venv + pip + yt-dlp，brew 安装 yt-dlp/aria2（若有 brew）
./scripts/install-mac.sh

# 同时用 Docker 部署 aria2 + Alist
./scripts/install-mac.sh --with-docker
```

安装完成后手动启动：

```bash
./scripts/start.sh
```

浏览器访问：http://127.0.0.1:8766  
组件状态：http://127.0.0.1:8766/components

---

## 三、下载组件部署方式

### 3.1 yt-dlp（必选，音视频）

**方式 A — pip（install-mac 已包含）**

```bash
source .venv/bin/activate
pip install yt-dlp
```

**方式 B — Homebrew**

```bash
brew install yt-dlp
```

在 `config.yaml` 中确认：

```yaml
engines:
  ytdlp_path: yt-dlp   # 若在 PATH 中即可
```

### 3.2 aria2（可选，HTTP/磁力/BT）

**方式 A — Homebrew（本机进程）**

```bash
brew install aria2
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800
```

**方式 B — Docker（生产推荐，与 compose 一致）**

```bash
docker compose up -d aria2
```

`config.yaml`：

```yaml
engines:
  aria2:
    rpc_url: http://127.0.0.1:6800/jsonrpc
    secret: mydownloader   # 与 docker-compose 中 RPC_SECRET 一致
```

### 3.3 Alist（可选，网盘）

仅通过 Docker：

```bash
docker compose up -d alist
```

首次访问 http://127.0.0.1:5244 查看日志中的管理员密码，登录后在后台获取 Token。

`config.yaml`：

```yaml
engines:
  alist:
    enabled: true
    url: http://127.0.0.1:5244
    token: "<你的 token>"
```

### 3.4 Docker 与下载目录对齐

`docker-compose.yml` 中 aria2 下载目录为 `./data/downloads`。若希望与主应用 `downloads/` 统一，可修改 compose 卷挂载，例如：

```yaml
volumes:
  - ./downloads:/downloads
```

并确保 aria2 任务输出到该路径（视 aria2 镜像配置而定）。

---

## 四、生产配置建议

编辑 `config.yaml`：

```yaml
server:
  host: 0.0.0.0          # 局域网可访问；仅本机用 127.0.0.1
  port: 8766
  api_key: "请设置强密钥"  # 生产务必设置

download:
  default_dir: downloads # 或绝对路径，如 /Users/you/Data/MyDownloader
  max_concurrent: 3

files:
  public_access: true
  public_base_url: "http://192.168.x.x:8766"  # 局域网 IP 或域名
```

Web 设置页可保存 API Key；浏览器端会写入 `localStorage` 供管理接口使用。

---

## 五、launchd 常驻（开机自启）

**一键安装（推荐）**

```bash
cd ~/MXDownloader
./scripts/install-mac.sh          # 若尚未安装依赖
./scripts/install-launchd.sh      # 安装开机自启并启动
```

或双击 `install-launchd.command`。

**重启服务**

```bash
./scripts/restart.sh
```

或双击 `restart.command`。

**卸载开机自启**

```bash
./scripts/install-launchd.sh --uninstall
```

---

### 手动安装（可选）

1. 先完成 `./scripts/install-mac.sh`（确保存在 `.venv`）

2. 复制并编辑 plist：

```bash
PROJECT_ROOT="$(pwd)"
sed "s|__PROJECT_ROOT__|${PROJECT_ROOT}|g" deploy/mydownloader.plist \
  > ~/Library/LaunchAgents/com.mydownloader.service.plist
```

3. 加载服务：

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mydownloader.service.plist
launchctl kickstart -k gui/$(id -u)/com.mydownloader.service
```

4. 查看状态 / 日志：

```bash
launchctl list | grep mydownloader
tail -f logs/launchd.out.log logs/launchd.err.log
```

5. 停止 / 卸载：

```bash
./scripts/install-launchd.sh --uninstall
```

若使用 Docker 组件，建议为 Docker Desktop 开启「登录时启动」，或单独为 compose 项目配置 launchd。

---

## 六、验证清单

| 检查项 | 命令 / 地址 |
|--------|-------------|
| 健康检查 | `curl http://127.0.0.1:8766/health` |
| 组件状态 | 打开 `/components`，yt-dlp / aria2 / alist 应为可用 |
| 试下载 | 仪表盘粘贴 B 站 / YouTube 链接 |
| 文件管理 | `/files` 列表与 `/files/xxx` 外链下载 |
| API Key | 设置 Key 后，无 Key 的 `POST /api/v1/downloads` 应返回 401 |

---

## 七、常见问题

**Q: brew install yt-dlp 报错 deno / Xcode 15？**

macOS 12（Monterey）上 **不要用 brew 装 yt-dlp**。用 pip（`install-mac.sh` 已自动执行）：

```bash
source .venv/bin/activate
pip install -U yt-dlp
```

在 Web **设置 → yt-dlp** 中，路径填：

```text
/Users/你的用户名/MXDownloader/.venv/bin/yt-dlp
```

**Q: macOS 12 安装 Python / Homebrew 很慢或失败？**

不要用 `brew install python@3.12`（可能编译数小时）。改用官方安装包：

1. https://www.python.org/downloads/macos/ 下载 Python 3.12
2. 安装后执行：

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 --version
cd ~/MXDownloader
rm -rf .venv
./scripts/install-mac.sh --skip-brew
```

**Q: pip install 报错 requires Python >=3.10，当前 3.9.6？**

系统自带 Python 太旧。安装并使用 Homebrew Python：

```bash
brew install python@3.12
# 若之前用 3.9 建过 venv，先删除
rm -rf .venv
./scripts/install-mac.sh
```

**Q: 双击 `start.command` 提示无法打开？**

```bash
chmod +x start.command scripts/start.sh
xattr -d com.apple.quarantine start.command  # 若被 Gatekeeper 拦截
```

**Q: aria2 显示无法连接 RPC？**

确认 aria2 进程或 Docker 容器在运行，且 `rpc_url`、`secret` 与 aria2 配置一致。

**Q: 其他设备无法访问？**

`server.host` 须为 `0.0.0.0`，并检查 macOS 防火墙是否放行 8766。

**Q: 与 Windows 开发环境差异？**

- 路径使用 `/`，无 GBK 编码问题
- 端口占用用 `lsof`（`start.sh` 已处理）
- 生产常驻用 launchd，而非 Windows 服务或 bat

---

## 八、与 AI 工具集成（可选）

- WorkBuddy Skill：`cp -r skills/mydownloader ~/.workbuddy/skills/mydownloader`
- Cursor MCP：在 MCP 配置中将路径改为 Mac 上的项目绝对路径，并设置 `MYDOWNLOADER_URL`

主 README 中有 MCP JSON 示例，将 `D:/...` 替换为 Mac 路径即可。

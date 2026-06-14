---
name: mydownloader
description: 通过本地 MyDownloader 服务下载音视频、HTTP 文件、网盘资源，并管理多媒体播放列表（yt-dlp / aria2 / Alist）
version: 1.1.0
author: mydownloader
tags: [download, yt-dlp, aria2, alist, 网盘, 音视频, 多媒体, 播放列表]
trigger_keywords: [下载, 音视频, 网盘, yt-dlp, 磁力, 离线下载, 多媒体, 播放列表, 轮播]
---

# MyDownloader Skill

通过本地 REST API 调用 MyDownloader 服务，统一下载音视频、HTTP 直链、磁力链接和网盘资源。

## 前置条件

1. MyDownloader 服务已启动（默认 `http://127.0.0.1:18026`）
2. 支持直接粘贴分享文案，服务会自动提取其中的链接
3. 对应引擎可用：
   - **yt-dlp**：YouTube、Bilibili、抖音等音视频站点
   - **aria2**：HTTP/HTTPS 直链、磁力链接
   - **Alist**：网盘分享链接（需在设置中启用并配置 Alist）

健康检查：`GET http://127.0.0.1:18026/health`

若配置了 API Key，所有 API 请求需携带请求头：`X-API-Key: <your-key>`

## 工作流程

1. **创建下载任务**
   ```http
   POST /api/v1/downloads
   Content-Type: application/json

   {
     "url": "https://www.bilibili.com/video/BV1xx",
     "engine": "ytdlp",
     "options": { "audio_only": false },
     "output_dir": "downloads"
   }
   ```

2. **轮询任务状态**（每 2–5 秒）
   ```http
   GET /api/v1/tasks/{id}
   ```

3. **任务完成**：`status` 为 `completed` 时，从响应的 `file_path` 获取本地文件路径。

4. **失败处理**：`status` 为 `failed` 时，查看 `error_message`；检查 `/health` 确认引擎状态。

## 引擎选择指南

| 场景 | engine | 说明 |
|------|--------|------|
| YouTube / Bilibili / 抖音 / Twitter 等 | `ytdlp` 或留空自动 | 支持 `options.format`、`audio_only`、`subtitle` |
| HTTP/HTTPS 直链 | `aria2` | 需 aria2 RPC 可用 |
| 磁力链接 `magnet:` | `aria2` | 需 aria2 支持 BT |
| Alist 分享链接 | `alist` | 需 Alist 已启用 |
| Alist 内部路径 | `alist` + `options.alist_path` | 如 `alist:///path/to/file` |

## options 示例

```json
{
  "audio_only": true,
  "format": "bestvideo+bestaudio",
  "subtitle": true,
  "cookies_file": "D:/cookies.txt",
  "alist_path": "/阿里云盘/视频.mp4",
  "offline_to_alist": false
}
```

## 管理任务

- 暂停：`POST /api/v1/tasks/{id}/pause`
- 取消：`POST /api/v1/tasks/{id}/cancel`
- 列表：`GET /api/v1/tasks?status=running`

## 多媒体中心 / 播放列表

下载完成的**视频/音频**会自动加入默认播放列表「全部下载」。也可创建自定义列表供轮播或播放。

### 查询（免 API Key）

```http
GET /api/v1/playlists
GET /api/v1/playlists/default/items
GET /api/v1/playlists/{id}/items
GET /api/v1/media/files
```

条目中的 `public_url` 可直接用于 `<video>` / 外部播放器轮播。

### 管理（需 API Key，若已配置）

```http
POST /api/v1/playlists
Body: { "name": "晚间轮播" }

POST /api/v1/playlists/{id}/items
Body: { "rel_path": "video.mp4" }
或: { "task_id": 3 }

DELETE /api/v1/playlists/{id}
DELETE /api/v1/playlists/{id}/items/{item_id}
```

### 典型场景

| 用户意图 | 操作 |
|----------|------|
| 查看可轮播内容 | `GET /api/v1/playlists/default/items` |
| 创建专题列表 | `POST /api/v1/playlists` → `POST .../items` |
| 把刚下载的视频加入列表 | `POST .../items` + `task_id` 或 `rel_path` |
| 浏览下载目录中的媒体 | `GET /api/v1/media/files` |

Web 管理页：`http://127.0.0.1:18026/media`

## 错误处理

| 错误 | 处理 |
|------|------|
| Engine not available | 检查 `/health`，安装或启动对应工具 |
| Alist is not enabled | 在 Web 设置页启用 Alist 并配置 URL/Token |
| 401 Invalid API key | 添加 `X-API-Key` 请求头 |
| 连接失败 | 确认服务运行在 127.0.0.1:18026 |

详细 API 见 `references/api.md`。

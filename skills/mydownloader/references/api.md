# MyDownloader API Reference

Base URL: `http://127.0.0.1:18026`

## Authentication

Optional. When `api_key` is set in settings, include:

```
X-API-Key: your-api-key
```

## Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "engines": {
    "ytdlp": true,
    "aria2": false,
    "alist": false
  }
}
```

### Create Download

```
POST /api/v1/downloads
```

Body:
```json
{
  "url": "string (required)",
  "engine": "ytdlp | aria2 | alist (optional)",
  "options": {},
  "output_dir": "optional absolute path"
}
```

Response: Task object.

### List Tasks

```
GET /api/v1/tasks?status=running
GET /api/v1/tasks?tab=active|completed|failed|all
```

### Task Counts

```
GET /api/v1/tasks/counts
```

### Delete Task

```
DELETE /api/v1/tasks/{id}?delete_file=false
```

Only for completed / failed / cancelled tasks. `delete_file=true` also removes the downloaded file.

### Get Task

```
GET /api/v1/tasks/{id}
```

### Pause Task

```
POST /api/v1/tasks/{id}/pause
```

### Cancel Task

```
POST /api/v1/tasks/{id}/cancel
```

### Get Settings

```
GET /api/v1/settings
```

### Engine Status

```
GET /api/v1/engines
```

Returns download directory, concurrency, and detailed status for yt-dlp / aria2 / alist.

```
GET /api/v1/engines/{name}
POST /api/v1/engines/{name}/test
```

`name`: `ytdlp` | `aria2` | `alist`

### Update Settings

```
PUT /api/v1/settings
```

Body (partial):
```json
{
  "download": { "default_dir": "downloads", "max_concurrent": 3 },
  "engines": {
    "ytdlp_path": "yt-dlp",
    "aria2": { "rpc_url": "http://127.0.0.1:6800/jsonrpc", "secret": "" },
    "alist": { "enabled": true, "url": "http://127.0.0.1:5244", "token": "" }
  }
}
```

## Task Object

```json
{
  "id": 1,
  "url": "https://...",
  "title": "filename",
  "source_type": "ytdlp",
  "status": "running",
  "progress": 45.5,
  "speed": "1.2MiB/s",
  "file_path": "<项目目录>/downloads/task_1_video.mp4",
  "file_size": 1048576,
  "engine_task_id": "abc123",
  "options": {},
  "output_dir": "<项目目录>/downloads",
  "error_message": "",
  "created_at": "2026-06-14T10:00:00",
  "updated_at": "2026-06-14T10:01:00"
}
```

## Status Values

`pending` | `running` | `completed` | `failed` | `paused` | `cancelled`

## Playlists (Multimedia Center)

Read endpoints are **public** (no API key). Write endpoints require `X-API-Key` when configured.

### List Playlists

```
GET /api/v1/playlists
```

### Default Playlist

```
GET /api/v1/playlists/default
GET /api/v1/playlists/default/items
```

Default playlist auto-collects completed video/audio downloads.

### Playlist Items (for carousel / rotation)

```
GET /api/v1/playlists/{id}/items
```

Each item includes `public_url` for direct playback:

```json
{
  "id": 1,
  "playlist_id": 1,
  "rel_path": "video.mp4",
  "title": "My Video",
  "name": "video.mp4",
  "size": 1048576,
  "media_type": "video",
  "task_id": 3,
  "sort_order": 1,
  "public_url": "http://127.0.0.1:18026/files/video.mp4",
  "exists": true,
  "added_at": "2026-06-14T10:00:00"
}
```

### List Media Files in Download Directory

```
GET /api/v1/media/files
```

### Create Playlist

```
POST /api/v1/playlists
Body: { "name": "My List" }
```

### Delete Playlist

```
DELETE /api/v1/playlists/{id}
```

Cannot delete the default playlist.

### Add Item

```
POST /api/v1/playlists/{id}/items
Body: { "rel_path": "subdir/video.mp4" }
或: { "task_id": 1 }
```

### Remove Item

```
DELETE /api/v1/playlists/{id}/items/{item_id}
```

### Reload from Disk

Scan the download directory and sync the playlist (add new media files, remove entries whose files were deleted). Does not modify download tasks.

```
POST /api/v1/playlists/{id}/reload
POST /api/v1/playlists/default/reload
```

Response:

```json
{
  "added": 2,
  "removed": 1,
  "item_count": 5,
  "message": "新增 2 个、移除 1 个"
}
```

## MCP Tools (Cursor)

When using `mcp_server/server.py`, these tools manage playlists:

| Tool | Description |
|------|-------------|
| `list_playlists` | All playlists |
| `list_playlist_items` | Items in default or specified playlist |
| `list_media_files` | Media files in download directory |
| `create_playlist` | Create playlist by name |
| `delete_playlist` | Delete custom playlist |
| `add_playlist_item` | Add by `rel_path` or `task_id` |
| `remove_playlist_item` | Remove item from playlist |

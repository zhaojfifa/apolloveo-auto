# HOT_FOLLOW_API_CONTRACT_v1

## POST /api/tasks/probe
**Request**
```json
{
  "platform": "douyin|tiktok|reels|xhs|auto",
  "url": "https://..."
}
```
**Response**
```json
{
  "platform": "douyin",
  "url": "https://...",
  "title": "...",
  "cover": "https://...",
  "duration_sec": 15,
  "source_id": "optional",
  "raw": {"any":"optional"},
  "raw_downloaded": false
}
```
Notes: must not create a task; must not download raw.

## POST /api/tasks (kind=hot_follow)
**Request**
```json
{
  "source_url": "https://...",
  "platform": "douyin",
  "kind": "hot_follow",
  "category_key": "hot_follow",
  "title": "optional",
  "content_lang": "mm",
  "ui_lang": "zh"
}
```
**Response**
- TaskDetail (task_id, status, etc.)

## POST /api/tasks/{task_id}/bgm
**Request (multipart)**
- `bgm_file` (mp3/wav)
- `mix_ratio` (0.0¨C1.0)
- `strategy` (replace|keep|mute)

**Response**
```json
{
  "task_id": "...",
  "bgm_key": "tasks/.../bgm/user_bgm.mp3",
  "mix_ratio": 0.8,
  "strategy": "replace"
}
```

## Step Endpoints (existing)
- POST `/api/tasks/{task_id}/parse`
- POST `/api/tasks/{task_id}/subtitles`
- POST `/api/tasks/{task_id}/dub`
- POST `/api/tasks/{task_id}/pack`
- POST `/api/tasks/{task_id}/scenes`
- POST `/api/tasks/{task_id}/publish`

## Publish Backfill
**Request**
```json
{
  "published": true,
  "published_url": "https://...",
  "notes": "optional"
}
```

## Deliverables (SSOT)
UI must treat deliverables as truth source:
- `publish_key` or `publish_url` with `publish_status=ready`
- `pack_path` / `pack_key`
- `scenes_path` / `scenes_key`

Deliverables list is exposed via:
- GET `/api/tasks/{task_id}/publish_hub`

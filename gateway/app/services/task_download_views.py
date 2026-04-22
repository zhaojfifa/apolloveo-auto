from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, Response

from gateway.app.config import get_settings
from gateway.app.services.artifact_storage import (
    get_download_url,
    get_object_bytes,
    object_exists,
)
from gateway.app.services.hot_follow_language_profiles import (
    hot_follow_audio_filename,
    hot_follow_subtitle_filename,
    hot_follow_subtitle_txt_filename,
)
from gateway.app.services.task_view_helpers import (
    task_endpoint,
    task_key,
    task_value,
)
from gateway.app.services.voice_state import hf_current_voiceover_asset


def require_storage_key(task: dict[str, Any], field: str, not_found: str) -> str:
    key = task_key(task, field)
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail=not_found)
    return key


def build_not_ready_response(
    task: dict[str, Any],
    artifact: str,
    missing: list[str],
    *,
    reason: str = "not_ready",
    status_code: int = 409,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "reason": reason,
            "task_id": str(task_value(task, "task_id") or task_value(task, "id") or ""),
            "artifact": artifact,
            "missing": missing,
            "status": {
                "subtitles": task_value(task, "subtitles_status"),
                "dub": task_value(task, "dub_status"),
                "scenes": task_value(task, "scenes_status"),
                "pack": task_value(task, "pack_status"),
                "publish": task_value(task, "publish_status"),
            },
            "hint": "Call generate or wait for pipeline to finish.",
            **(extra or {}),
        },
    )


def text_or_redirect(key: str, inline: bool) -> Response:
    if inline:
        data = get_object_bytes(key)
        if data is None:
            raise HTTPException(status_code=404, detail="artifact not found")
        return Response(content=data, media_type="text/plain; charset=utf-8")
    return RedirectResponse(url=get_download_url(key), status_code=302)


def build_deliverable_download_redirect(task_id: str, task: dict[str, Any], kind: str) -> RedirectResponse:
    target_lang = task.get("target_lang") or task.get("content_lang") or "mm"
    key = None
    filename = None
    content_type = None

    if kind == "raw":
        key = task_key(task, "raw_path")
        filename = "raw.mp4"
        content_type = "video/mp4"
    elif kind == "pack":
        key = task_value(task, "pack_key") or task_value(task, "pack_path")
        filename = "pack.zip"
        content_type = "application/zip"
    elif kind == "scenes":
        key = task_value(task, "scenes_pack_key") or task_value(task, "scenes_key")
        filename = "scenes.zip"
        content_type = "application/zip"
    elif kind == "final_mp4":
        key = task_key(task, "final_video_key") or task_key(task, "final_video_path")
        filename = "final.mp4"
        content_type = "video/mp4"
    elif kind == "origin_srt":
        key = task_key(task, "origin_srt_path")
        filename = "origin.srt"
        content_type = "application/x-subrip"
    elif kind == "mm_srt":
        key = task_key(task, "mm_srt_path")
        filename = hot_follow_subtitle_filename(target_lang)
        content_type = "application/x-subrip"
    elif kind == "mm_txt":
        mm_key = task_key(task, "mm_srt_path")
        if mm_key:
            key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
        filename = hot_follow_subtitle_txt_filename(target_lang)
        content_type = "text/plain"
    elif kind == "mm_audio":
        if str(task.get("kind") or "").strip().lower() == "hot_follow":
            asset = hf_current_voiceover_asset(task_id, task, get_settings())
            key = str(asset.get("key") or "").strip() or None
        else:
            key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
        filename = hot_follow_audio_filename(target_lang)
        content_type = "audio/mpeg"
    elif kind == "publish_bundle":
        return RedirectResponse(url=task_endpoint(task_id, "publish_bundle"), status_code=302)
    else:
        raise HTTPException(status_code=400, detail="Unsupported kind")

    if not key or not object_exists(str(key)):
        raise HTTPException(status_code=404, detail="Deliverable not found")
    url = get_download_url(
        str(key),
        disposition="attachment",
        filename=filename,
        content_type=content_type,
    )
    return RedirectResponse(url=url, status_code=302)

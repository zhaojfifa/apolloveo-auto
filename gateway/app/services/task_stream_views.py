"""Generic task stream/view helpers.

These helpers keep router modules focused on request handling while preserving
existing stream behavior and error responses.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse


def resolve_audio_meta(
    task_id: str,
    repo,
    *,
    task_value: Callable[[dict, str], Any],
    current_voiceover_asset_loader: Callable[[str, dict, Any], dict[str, Any]],
    settings_loader: Callable[[], Any],
    artifact_ready_assert: Callable[..., tuple[int, str | None]],
    object_exists_fn: Callable[[str], bool],
    object_head_fn: Callable[[str], Any],
) -> tuple[str, int, str]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="dubbed audio not found")
    if str(task_value(task, "kind") or "").strip().lower() == "hot_follow":
        asset = current_voiceover_asset_loader(task_id, task, settings_loader())
        chosen_key = str(asset.get("key") or "").strip() or None
        if not chosen_key:
            raise HTTPException(status_code=404, detail="voiceover_not_ready")
        try:
            chosen_size, chosen_type = artifact_ready_assert(
                kind="audio",
                key=chosen_key,
                exists_fn=object_exists_fn,
                head_fn=object_head_fn,
            )
        except Exception as exc:
            raise HTTPException(status_code=404, detail="voiceover_not_ready") from exc
        content_type = str(
            chosen_type or asset.get("content_type") or task_value(task, "mm_audio_mime") or "audio/mpeg"
        )
    else:
        chosen_key = task_value(task, "mm_audio_key") or task_value(task, "mm_audio_path")
        if not chosen_key:
            raise HTTPException(status_code=404, detail="voiceover_not_ready")
        try:
            chosen_size, chosen_type = artifact_ready_assert(
                kind="audio",
                key=str(chosen_key),
                exists_fn=object_exists_fn,
                head_fn=object_head_fn,
            )
        except Exception as exc:
            raise HTTPException(status_code=404, detail="voiceover_not_ready") from exc
        content_type = str(chosen_type or task_value(task, "mm_audio_mime") or "audio/mpeg")
    return str(chosen_key), int(chosen_size), content_type


def resolve_final_meta(
    task_id: str,
    repo,
    *,
    task_value: Callable[[dict, str], Any],
    deliver_key_builder: Callable[[str, str], str],
    object_exists_fn: Callable[[str], bool],
    object_head_fn: Callable[[str], Any],
    media_meta_from_head_fn: Callable[[Any], tuple[int, str | None]],
) -> tuple[str, int, str]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="final video not found")
    key = (
        task_value(task, "final_video_key")
        or task_value(task, "final_video_path")
        or deliver_key_builder(task_id, "final.mp4")
    )
    if not key or not object_exists_fn(str(key)):
        raise HTTPException(status_code=404, detail="final video not found")
    head = object_head_fn(str(key))
    total, ctype = media_meta_from_head_fn(head)
    if total <= 0:
        raise HTTPException(status_code=404, detail="final video not found")
    content_type = str(task_value(task, "final_mime") or ctype or "video/mp4")
    return str(key), int(total), content_type


def parse_http_range(range_header: str, total: int) -> tuple[int, int]:
    match = re.match(r"bytes=(\d*)-(\d*)", (range_header or "").strip())
    if not match:
        raise ValueError("invalid_range")
    start_raw, end_raw = match.group(1), match.group(2)
    if start_raw == "" and end_raw == "":
        raise ValueError("invalid_range")
    if start_raw == "":
        suffix = int(end_raw)
        if suffix <= 0:
            raise ValueError("invalid_range")
        start = max(total - suffix, 0)
        end = total - 1
    else:
        start = int(start_raw)
        end = int(end_raw) if end_raw else total - 1
    if start >= total or start < 0 or end < start:
        raise ValueError("range_not_satisfiable")
    end = min(end, total - 1)
    return start, end


def build_stream_head_response(
    task_id: str,
    repo,
    *,
    resolve_meta: Callable[[str, Any], tuple[str, int, str]],
    logger,
    event_name: str,
    failure_log: str,
    failure_detail: str,
    default_content_type: str,
) -> Response:
    try:
        _, total, content_type = resolve_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception(failure_log, extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": failure_detail})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type or default_content_type,
        "Content-Length": str(total),
    }
    logger.info(
        event_name,
        extra={
            "task_id": task_id,
            "has_range": False,
            "start": 0,
            "end": total - 1,
            "total": total,
            "status": 200,
            "content_type": headers["Content-Type"],
        },
    )
    return Response(status_code=200, headers=headers)


def build_stream_download_response(
    task_id: str,
    request: Request,
    repo,
    *,
    resolve_meta: Callable[[str, Any], tuple[str, int, str]],
    parse_range: Callable[[str, int], tuple[int, int]],
    stream_object_range_loader: Callable[[str, int, int], tuple[Any, int]],
    logger,
    event_name: str,
    resolve_failure_log: str,
    resolve_failure_detail: str,
    stream_failure_log: str,
    stream_failure_detail: str,
) -> Response:
    try:
        key, total, content_type = resolve_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception(resolve_failure_log, extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": resolve_failure_detail})

    range_header = request.headers.get("range")
    start = 0
    end = total - 1
    status_code = 200
    if range_header:
        try:
            start, end = parse_range(range_header, total)
        except Exception:
            logger.info(
                event_name,
                extra={
                    "task_id": task_id,
                    "has_range": True,
                    "range_in": range_header,
                    "start": None,
                    "end": None,
                    "total": total,
                    "status": 416,
                    "content_type": content_type,
                },
            )
            return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
        status_code = 206
    try:
        stream, length = stream_object_range_loader(str(key), start, end)
    except ValueError:
        logger.info(
            event_name,
            extra={
                "task_id": task_id,
                "has_range": bool(range_header),
                "range_in": range_header,
                "start": start,
                "end": end,
                "total": total,
                "status": 416,
                "content_type": content_type,
            },
        )
        return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
    except Exception as exc:
        logger.exception(stream_failure_log, extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": stream_failure_detail})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
        "Content-Length": str(length),
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    logger.info(
        event_name,
        extra={
            "task_id": task_id,
            "has_range": bool(range_header),
            "range_in": range_header,
            "start": start,
            "end": end,
            "total": total,
            "status": status_code,
            "content_type": content_type,
        },
    )
    return StreamingResponse(stream, status_code=status_code, headers=headers, media_type=content_type)

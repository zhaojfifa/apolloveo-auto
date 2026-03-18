"""Media helpers: file hashing, URL probing, pipeline probe, BGM upload.

Extracted from tasks.py as part of Phase 1.3 Port Merge.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from gateway.app.services.artifact_storage import get_download_url, upload_task_artifact
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage

logger = logging.getLogger(__name__)


# ── File hashing ─────────────────────────────────────────────────────────────

def sha256_file(path: Path) -> str | None:
    """Return the SHA-256 hex digest of *path*, or ``None`` if it doesn't exist."""
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ── Upload helper ────────────────────────────────────────────────────────────

def save_upload_to_paths(
    *,
    upload: UploadFile,
    inputs_path: Path,
    raw_path_target: Path,
    max_bytes: int,
) -> int:
    """Stream *upload* to disk, enforcing a size limit."""
    inputs_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path_target.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with inputs_path.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                out.close()
                try:
                    inputs_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise HTTPException(status_code=413, detail="upload too large")
            out.write(chunk)
    if inputs_path != raw_path_target:
        shutil.copyfile(inputs_path, raw_path_target)
    return total


# ── BGM upload implementation ────────────────────────────────────────────────

def upload_task_bgm_impl(
    task_id: str,
    *,
    bgm_file: UploadFile,
    original_pct: int | None,
    bgm_pct: int | None,
    mix_ratio: float | None,
    strategy: str | None,
    repo,
) -> dict[str, Any]:
    """Handle BGM file upload for *task_id* and return the result dict."""
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not bgm_file or not bgm_file.filename:
        raise HTTPException(status_code=400, detail="bgm_file is required")

    ext = Path(bgm_file.filename).suffix.lower()
    if ext not in {".mp3", ".wav"}:
        raise HTTPException(status_code=400, detail="unsupported file type")

    max_mb = int(os.getenv("MAX_BGM_UPLOAD_MB", "50"))
    max_bytes = max_mb * 1024 * 1024

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / f"user_bgm{ext}"
        save_upload_to_paths(
            upload=bgm_file,
            inputs_path=tmp_path,
            raw_path_target=tmp_path,
            max_bytes=max_bytes,
        )
        artifact_name = f"bgm/user_bgm{ext}"
        bgm_key = upload_task_artifact(task, tmp_path, artifact_name, task_id=task_id)

    ratio = mix_ratio
    if ratio is None:
        if bgm_pct is not None and original_pct is not None:
            total = max(bgm_pct + original_pct, 0)
            ratio = (bgm_pct / total) if total > 0 else 0.5
        else:
            ratio = 0.8
    ratio = max(0.0, min(float(ratio), 1.0))

    config = dict(task.get("config") or {})
    config["bgm"] = {
        "strategy": strategy or "replace",
        "bgm_key": bgm_key,
        "mix_ratio": ratio,
    }
    policy_upsert(repo, task_id, None, {"config": config}, step="media_helpers.bgm")

    bgm_url = get_download_url(str(bgm_key)) if bgm_key else None
    return {
        "task_id": task_id,
        "bgm_key": bgm_key,
        "bgm_url": bgm_url,
        "mix_ratio": ratio,
        "strategy": config["bgm"]["strategy"],
    }


# ── Pipeline probe merge ─────────────────────────────────────────────────────

def merge_probe_into_pipeline_config(
    pipeline_config: dict[str, str], probe: dict[str, Any] | None
) -> dict[str, str]:
    """Merge subtitle probe results into an existing pipeline config dict."""
    if not probe:
        return pipeline_config
    kind = probe.get("subtitle_track_kind")
    if isinstance(kind, str) and kind:
        pipeline_config["subtitle_track_kind"] = kind
    has_sub = probe.get("has_subtitle_stream")
    if has_sub is True:
        pipeline_config["subtitle_stream"] = "true"
    elif has_sub is False:
        pipeline_config["subtitle_stream"] = "false"
    subtitle_codecs = probe.get("subtitle_codecs") or []
    if isinstance(subtitle_codecs, list) and subtitle_codecs:
        pipeline_config["subtitle_codecs"] = ",".join(
            [str(v) for v in subtitle_codecs if str(v).strip()]
        )
    return pipeline_config


def update_pipeline_probe(
    repo, task_id: str, probe: dict[str, Any] | None
) -> None:
    """Merge probe data into a task's pipeline_config and persist if changed."""
    if not probe:
        return
    task = repo.get(task_id)
    if not task:
        return
    current = parse_pipeline_config(task.get("pipeline_config"))
    updated = merge_probe_into_pipeline_config(current, probe)
    if updated != current:
        policy_upsert(
            repo, task_id, None,
            {"pipeline_config": pipeline_config_to_storage(updated)},
            step="media_helpers.probe",
        )


# ── URL probe ────────────────────────────────────────────────────────────────

async def probe_url_metadata(
    url: str, platform_hint: str | None = None
) -> dict[str, Any]:
    """Probe a social-media URL for metadata without creating a task."""
    import re
    from gateway.app.services.parse import detect_platform
    from gateway.app.providers.xiongmao import XiongmaoError, parse_with_xiongmao

    def _extract_first_http_url(text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"https?://\S+", text)
        return match.group(0) if match else None

    url = _extract_first_http_url(url) or url
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    platform = (platform_hint or "").strip().lower() if platform_hint else "auto"
    if platform in ("", "auto"):
        platform = detect_platform(url) or "auto"
    logger.info("[hotfollow][probe] source_url=%s", url)
    logger.info("[hotfollow][probe] platform=%s", platform or "auto")

    try:
        meta = await parse_with_xiongmao(url, platform_hint=platform)
    except XiongmaoError as exc:
        logger.warning(
            "[hotfollow][probe] provider=xiongmao resolved_url=%s error=%s",
            url,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw = meta.get("raw") if isinstance(meta, dict) else None
    duration_sec = None
    if isinstance(raw, dict):
        for key in ("duration_sec", "duration", "durationSec"):
            if raw.get(key):
                try:
                    duration_sec = int(float(raw.get(key)))
                    break
                except Exception:
                    pass

    return {
        "platform": platform or meta.get("platform"),
        "url": url,
        "title": meta.get("title") if isinstance(meta, dict) else None,
        "cover": meta.get("cover") if isinstance(meta, dict) else None,
        "duration_sec": duration_sec,
        "source_id": raw.get("source_id") if isinstance(raw, dict) else None,
        "raw": raw,
        "raw_downloaded": False,
    }

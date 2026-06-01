"""Matrix Script minimal-result artifact staged persistence (PR-16R).

Promotes a local result pack (final.mp4 / manifest / subtitles / audio / scene
clips) from ``local_workspace`` to ``artifact_staged`` by copying each file
through an injected artifact sink and recording opaque ``artifact://`` refs.

This is staging, NOT publish: ``delivery_candidate=True`` but
``official_publish_ready=False``. No provider URL / Akool id / model / credit;
no ``publish_url`` / ``publish_status``; a provider temporary URL is never a
deliverable (real provider outputs are copied to local files first by the
generation step, then staged here as Apollo artifacts).

Sinks: tests inject an in-memory fake. Production wiring (PR-17R) injects a sink
that delegates to the existing ``artifact_storage`` abstraction — this module
does NOT modify ``artifact_storage.py``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

LINE_ID = "matrix_script"
STORAGE_SCOPE_STAGED = "artifact_staged"
GENERATION_PROVIDER_NONE = "none"
ARTIFACT_REF_PREFIX = "artifact://"

# Tokens that must never appear in a staging record (provider/publish leakage).
FORBIDDEN_TOKENS = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor",
    "model_id", "credit", "provider_task_id", "publish_url", "publish_status",
)


class StagingError(ValueError):
    """Raised on an invalid staging input."""


@dataclass(frozen=True)
class MatrixScriptStagedArtifactRef:
    """One staged artifact: its local source + opaque Apollo artifact ref."""

    kind: str
    local_path: str
    artifact_ref: str
    storage_scope: str = STORAGE_SCOPE_STAGED


@dataclass(frozen=True)
class MatrixScriptMinimalResultStagingRecord:
    """Staged result record — a delivery candidate, NOT publish-ready."""

    task_id: Optional[str]
    final_video_artifact_ref: str
    manifest_artifact_ref: str
    subtitles_artifact_ref: str
    audio_artifact_ref: str
    scene_clip_artifact_refs: Tuple[str, ...]
    line_id: str = LINE_ID
    storage_scope: str = STORAGE_SCOPE_STAGED
    delivery_candidate: bool = True
    official_publish_ready: bool = False
    generation_provider: str = GENERATION_PROVIDER_NONE
    scene_clips_staged: bool = True
    # Operator-accessible browser preview URL for the staged final video, when
    # the sink can produce one (e.g. /files/<key> for local, presigned for R2).
    # NOT a provider/temporary/publish URL — an internal staged preview.
    final_video_preview_url: Optional[str] = None


class InMemoryArtifactSink:
    """Test/default sink: records puts, returns an opaque ``artifact://`` ref.

    Does NOT read the file bytes (staging is exercised offline). The production
    sink (PR-17R) wraps the existing artifact_storage abstraction instead.
    """

    def __init__(self) -> None:
        self.puts: List[Tuple[str, str]] = []  # (local_path, artifact_name)

    def put(self, local_path: str, artifact_name: str) -> str:
        if not isinstance(local_path, str) or not local_path:
            raise StagingError("local_path must be a non-empty string")
        if not isinstance(artifact_name, str) or not artifact_name:
            raise StagingError("artifact_name must be a non-empty string")
        self.puts.append((local_path, artifact_name))
        return f"{ARTIFACT_REF_PREFIX}{artifact_name}"

    def preview_url_for(self, artifact_name: str) -> str:
        """Browser-openable preview URL (fake local-style path for tests)."""
        return f"/files/{artifact_name}"


def _artifact_name(task_id: Optional[str], kind: str, local_path: str) -> str:
    tid = task_id or "unknown"
    return f"{LINE_ID}/{tid}/{kind}/{os.path.basename(local_path)}"


def _stage_one(sink: Any, task_id: Optional[str], kind: str, local_path: str) -> str:
    if not isinstance(local_path, str) or not local_path:
        raise StagingError(f"{kind}: local_path must be a non-empty string")
    if not os.path.exists(local_path):
        raise StagingError(f"{kind}: local file does not exist: {local_path}")
    return sink.put(local_path, _artifact_name(task_id, kind, local_path))


def stage_minimal_result(
    *,
    sink: Any,
    task_id: Optional[str],
    final_video_path: str,
    manifest_path: str,
    subtitles_path: str,
    audio_path: str,
    scene_clip_paths: Tuple[str, ...] = (),
    stage_scene_clips: bool = True,
) -> MatrixScriptMinimalResultStagingRecord:
    """Stage the result pack via ``sink`` and return the staged record.

    ``final.mp4`` is mandatory — a missing one fails clearly. Scene clips are
    staged when ``stage_scene_clips`` (default) else recorded local-only with
    ``scene_clips_staged=False``.
    """
    if sink is None or not hasattr(sink, "put"):
        raise StagingError("sink must provide a put(local_path, artifact_name) method")

    final_name = _artifact_name(task_id, "final", final_video_path)
    final_ref = _stage_one(sink, task_id, "final", final_video_path)
    manifest_ref = _stage_one(sink, task_id, "manifest", manifest_path)
    subtitles_ref = _stage_one(sink, task_id, "subtitles", subtitles_path)
    audio_ref = _stage_one(sink, task_id, "audio", audio_path)

    # Operator-accessible preview URL for the final video, when the sink can
    # produce one (browser-openable; never a provider/temporary/publish URL).
    final_preview_url: Optional[str] = None
    if hasattr(sink, "preview_url_for"):
        try:
            candidate = sink.preview_url_for(final_name)
            if isinstance(candidate, str) and candidate:
                final_preview_url = candidate
        except Exception:
            final_preview_url = None

    clip_refs: List[str] = []
    if stage_scene_clips:
        for clip in scene_clip_paths:
            clip_refs.append(_stage_one(sink, task_id, "scene", clip))

    record = MatrixScriptMinimalResultStagingRecord(
        task_id=task_id,
        final_video_artifact_ref=final_ref,
        manifest_artifact_ref=manifest_ref,
        subtitles_artifact_ref=subtitles_ref,
        audio_artifact_ref=audio_ref,
        scene_clip_artifact_refs=tuple(clip_refs),
        scene_clips_staged=bool(stage_scene_clips),
        final_video_preview_url=final_preview_url,
    )
    assert_no_staging_forbidden_tokens(staging_record_to_dict(record))
    return record


def staging_record_to_dict(record: MatrixScriptMinimalResultStagingRecord) -> Dict[str, object]:
    return {
        "task_id": record.task_id,
        "line_id": record.line_id,
        "storage_scope": record.storage_scope,
        "final_video_artifact_ref": record.final_video_artifact_ref,
        "manifest_artifact_ref": record.manifest_artifact_ref,
        "subtitles_artifact_ref": record.subtitles_artifact_ref,
        "audio_artifact_ref": record.audio_artifact_ref,
        "scene_clip_artifact_refs": list(record.scene_clip_artifact_refs),
        "scene_clips_staged": record.scene_clips_staged,
        "delivery_candidate": record.delivery_candidate,
        "official_publish_ready": record.official_publish_ready,
        "generation_provider": record.generation_provider,
        "final_video_preview_url": record.final_video_preview_url,
    }


def assert_no_staging_forbidden_tokens(payload: object) -> None:
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        key_hits = [t for t in FORBIDDEN_TOKENS if t in keys_blob]
        if key_hits:
            raise StagingError(f"staging record has forbidden keys: {key_hits}")
    value_hits = [t for t in FORBIDDEN_TOKENS if t in str(payload).lower()]
    if value_hits:
        raise StagingError(f"staging record leaks forbidden tokens: {value_hits}")

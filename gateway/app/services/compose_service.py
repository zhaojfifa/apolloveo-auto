"""CompositionService — extracted from _hf_compose_final_video (TASK-2.0).

Separates pre-validation, FFmpeg execution, and post-persistence into
distinct methods.  Every subprocess.run call goes through _run_ffmpeg()
which enforces a configurable timeout.

Historical bug-fix preservation:
  - datetime: module-level import only, no local shadowing (bb73f5d)
  - empty SRT: subtitle_only_compose guard ported verbatim (267744a)
  - exception cascade: unchanged in caller tasks.py (76e15a3)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from gateway.app.services.artifact_storage import object_exists, object_head
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.media_helpers import sha256_file
from gateway.app.services.hot_follow_media_policy import (
    hot_follow_compose_scale_expr,
    hot_follow_media_input_policy,
)
from gateway.app.services.media_validation import (
    MIN_VIDEO_BYTES,
    assert_artifact_ready,
    assert_local_audio_ok,
    assert_local_video_ok,
    deliver_key,
    media_meta_from_head,
)
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.services.compose_subtitle_rendering import (
    compose_subtitle_vf,
    escape_subtitles_path,
    optimize_hot_follow_subtitle_layout_srt,
    source_subtitle_cover_filter,
    subtitle_render_signature,
)
from gateway.app.services.voice_state import DRY_TTS_CONFIG_KEY, collect_voice_execution_state
from gateway.app.services.worker_gateway import WorkerExecutionMode, WorkerRequest
from gateway.app.services.worker_gateway_registry import get_worker_gateway
from gateway.app.services.task_view_helpers import task_endpoint, task_key
from gateway.app.core.constants import COMPOSE_RETRY_AFTER_MS
from gateway.app.services.compose_helpers import task_compose_lock
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)

_SOURCE_AUDIO_BED_VOLUME_FLOOR = 0.35

# ---------------------------------------------------------------------------
# Module-level pure helpers (extracted from nested functions)
# ---------------------------------------------------------------------------


def _current_final_is_fresh(
    task: dict,
    *,
    revision: dict[str, str | None],
    final_exists: bool,
    final_size: int,
) -> bool:
    """Return True only if the existing final incorporates the current subtitle + audio.

    When True the compose service may safely skip re-running FFmpeg.
    When False compose must run regardless of whether a file physically exists.
    """
    if not final_exists or final_size < MIN_VIDEO_BYTES:
        return False
    compose_last_status = str(
        task.get("compose_last_status") or task.get("compose_status") or ""
    ).strip().lower()
    if compose_last_status not in {"done", "ready", "success", "completed"}:
        return False

    current_audio_sha = str(revision.get("audio_sha256") or "").strip() or None
    current_sub_hash = str(revision.get("subtitle_content_hash") or "").strip() or None
    current_sub_at = str(revision.get("subtitle_updated_at") or "").strip() or None
    current_render_signature = str(revision.get("render_signature") or "").strip() or None
    current_source_audio_policy = str(revision.get("source_audio_policy") or "mute").strip().lower() or "mute"
    current_dub_at = str(task.get("dub_generated_at") or "").strip() or None
    composed_audio_sha = str(task.get("final_source_audio_sha256") or "").strip() or None
    composed_dub_at = str(task.get("final_source_dub_generated_at") or "").strip() or None
    composed_sub_hash = str(task.get("final_source_subtitles_content_hash") or "").strip() or None
    composed_sub_at = str(task.get("final_source_subtitle_updated_at") or "").strip() or None
    composed_render_signature = str(task.get("final_source_render_signature") or "").strip() or None
    composed_source_audio_policy = str(task.get("final_source_audio_policy") or "").strip().lower() or None
    compose_finished_at = str(task.get("compose_last_finished_at") or task.get("final_updated_at") or "").strip() or None

    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    # No compose snapshot → cannot confirm what was baked into the final → recompose.
    if (
        not composed_audio_sha
        and not composed_sub_hash
        and not composed_dub_at
        and not composed_sub_at
        and not composed_render_signature
        and not composed_source_audio_policy
    ):
        return False

    if composed_audio_sha and current_audio_sha and composed_audio_sha != current_audio_sha:
        return False
    if composed_dub_at and current_dub_at and composed_dub_at != current_dub_at:
        return False
    if current_dub_at and compose_finished_at:
        current_dub_dt = _parse_dt(current_dub_at)
        compose_finished_dt = _parse_dt(compose_finished_at)
        if current_dub_dt is not None and compose_finished_dt is not None and current_dub_dt > compose_finished_dt:
            return False
    if composed_sub_hash and current_sub_hash:
        if composed_sub_hash != current_sub_hash:
            return False
    if composed_sub_at and current_sub_at and composed_sub_at != current_sub_at:
        return False
    if composed_render_signature and current_render_signature and composed_render_signature != current_render_signature:
        return False
    if composed_source_audio_policy and composed_source_audio_policy != current_source_audio_policy:
        return False
    if not composed_source_audio_policy and current_source_audio_policy != "mute":
        return False
    if current_sub_at and compose_finished_at:
        current_sub_dt = _parse_dt(current_sub_at)
        compose_finished_dt = _parse_dt(compose_finished_at)
        if current_sub_dt is not None and compose_finished_dt is not None and current_sub_dt > compose_finished_dt:
            return False
    if not composed_sub_hash and not composed_sub_at and current_sub_hash:
        return False
    if not composed_render_signature and current_render_signature:
        return False
    return True


def _subtitle_content_hash(text: str | None) -> str | None:
    source = "" if text is None else str(text)
    if not source:
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _read_text_compat(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def compose_fail(
    reason: str,
    message: str,
    status_code: int = 409,
    *,
    ffmpeg_cmd: str | None = None,
    stderr_tail: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Raise HTTPException with structured compose error detail."""
    detail: dict[str, Any] = {"reason": reason, "message": message}
    if ffmpeg_cmd:
        detail["ffmpeg_cmd"] = ffmpeg_cmd
    if stderr_tail:
        detail["stderr_tail"] = stderr_tail
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=status_code, detail=detail)


def _with_live_hot_follow_subtitle_currentness(task_id: str, task: dict) -> dict:
    live_task = dict(task or {})
    if str(live_task.get("kind") or "").strip().lower() != "hot_follow":
        return live_task
    try:
        from gateway.app.services.hot_follow_runtime_bridge import compat_hot_follow_subtitle_lane_state

        subtitle_lane = compat_hot_follow_subtitle_lane_state(task_id, live_task)
    except Exception:
        logger.exception("HF_COMPOSE_SUBTITLE_CURRENTNESS_REFRESH_FAILED", extra={"task_id": task_id})
        return live_task

    live_task["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    live_task["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    return live_task


def _resolve_compose_video_key(task: dict, source_audio_policy: str) -> tuple[str | None, bool]:
    """Resolve compose video input and whether it can provide preserved source audio."""
    raw_key = task_key(task, "raw_path") or task_key(task, "raw_video_key")
    mute_key = task_key(task, "mute_video_key") or task_key(task, "mute_video_path")
    if str(source_audio_policy or "").strip().lower() == "preserve" and raw_key:
        return str(raw_key), True
    if mute_key:
        return str(mute_key), False
    if raw_key:
        return str(raw_key), str(source_audio_policy or "").strip().lower() == "preserve"
    return None, False


def _resolve_compose_voiceover_key(task: dict, voice_state: dict[str, Any]) -> str | None:
    if not bool(voice_state.get("audio_ready")):
        return None
    config = dict(task.get("config") or {})
    dry_audio_key = str(config.get(DRY_TTS_CONFIG_KEY) or "").strip() or None
    if dry_audio_key:
        return dry_audio_key
    legacy_audio_key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
    if not legacy_audio_key:
        return None
    bgm_key = str((dict(config.get("bgm") or {})).get("bgm_key") or "").strip() or None
    source_audio_keys = {
        str(value).strip()
        for value in (
            bgm_key,
            task_key(task, "raw_path"),
            task_key(task, "raw_video_key"),
            task_key(task, "mute_video_key"),
            task_key(task, "mute_video_path"),
        )
        if str(value or "").strip()
    }
    return None if str(legacy_audio_key).strip() in source_audio_keys else str(legacy_audio_key)


def _source_audio_bed_volume(value: float | None) -> float:
    try:
        mix = float(value if value is not None else _SOURCE_AUDIO_BED_VOLUME_FLOOR)
    except Exception:
        mix = _SOURCE_AUDIO_BED_VOLUME_FLOOR
    if mix <= 0:
        return _SOURCE_AUDIO_BED_VOLUME_FLOOR
    return max(0.0, min(1.0, mix))


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ComposeTimeouts:
    """Timeout values (seconds) for each FFmpeg stage."""

    freeze_tail: int = 120
    compose: int = 600
    probe: int = 30
    clamp: int = 120
    derive: int = 600


@dataclass(frozen=True)
class ComposeInputProfile:
    size_bytes: int
    duration_sec: float
    width: int | None = None
    height: int | None = None
    bit_rate: int | None = None
    pix_fmt: str | None = None

    @property
    def pixels(self) -> int | None:
        if not self.width or not self.height:
            return None
        return int(self.width) * int(self.height)

    def to_dict(self) -> dict[str, Any]:
        return {
            "size_bytes": self.size_bytes,
            "duration_sec": self.duration_sec,
            "width": self.width,
            "height": self.height,
            "bit_rate": self.bit_rate,
            "pix_fmt": self.pix_fmt,
            "pixels": self.pixels,
        }


@dataclass(frozen=True)
class ComposePlan:
    mute: bool = True
    overlay_subtitles: bool = True
    strip_subtitle_streams: bool = True
    cleanup_mode: str = "none"
    target_lang: str = "mm"
    freeze_tail_enabled: bool = False
    freeze_tail_cap_sec: int = 8
    compose_policy: str = "match_video"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mute": self.mute,
            "overlay_subtitles": self.overlay_subtitles,
            "strip_subtitle_streams": self.strip_subtitle_streams,
            "cleanup_mode": self.cleanup_mode,
            "target_lang": self.target_lang,
            "freeze_tail_enabled": self.freeze_tail_enabled,
            "freeze_tail_cap_sec": self.freeze_tail_cap_sec,
            "compose_policy": self.compose_policy,
        }


@dataclass(frozen=True)
class HotFollowComposeRequestContract:
    bgm_mix: float | None = None
    overlay_subtitles: bool | None = None
    freeze_tail_enabled: bool | None = None
    force: bool = False
    expected_subtitle_updated_at: str | None = None
    expected_audio_sha256: str | None = None


@dataclass(frozen=True)
class HotFollowComposeResponseContract:
    status_code: int
    body: dict[str, Any]


@dataclass(frozen=True)
class ComposeResult:
    updates: dict[str, Any]
    final_key: str
    final_url: str
    compose_status: str


@dataclass
class _ComposeInputs:
    """Validated inputs extracted from task dict."""

    video_key: str
    audio_key: str | None
    subtitle_only_compose: bool
    voice_state: dict
    bgm_key: str | None
    bgm_mix: float
    source_audio_policy: str
    source_audio_available: bool
    overlay_subtitles: bool
    strip_subtitle_streams: bool
    cleanup_mode: str
    target_lang: str
    freeze_tail_enabled: bool
    freeze_tail_cap_sec: float
    compose_policy: str
    ffmpeg: str


@dataclass
class _WorkspaceFiles:
    """Mutable workspace state for the compose pipeline."""

    task_id: str
    tmp: Path
    video_input_path: Path
    voice_path: Path | None
    final_path: Path
    subtitle_path: Path | None
    bgm_path: Path | None
    fontsdir: Path
    ffmpeg: str
    video_duration: float
    voice_duration: float
    compose_policy: str
    subtitle_key: str | None = None
    subtitle_object_etag: str | None = None
    subtitle_content_hash: str | None = None
    subtitle_sha256: str | None = None
    compose_warning: str | None = None
    ffmpeg_cmd_used: str | None = None
    overlay_subtitles: bool = True
    compose_input_policy: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# CompositionService
# ---------------------------------------------------------------------------


class CompositionService:
    """Orchestrates the final-video compose pipeline with timeout protection."""

    def __init__(
        self,
        *,
        storage: Any,
        settings: Any,
        timeouts: ComposeTimeouts | None = None,
    ) -> None:
        self._storage = storage
        self._settings = settings
        self._timeouts = timeouts or ComposeTimeouts()

    # ── Public entry point ────────────────────────────────────────────────

    def compose(
        self,
        task_id: str,
        task: dict,
        *,
        subtitle_resolver: Callable[[dict, str, str], str | None],
        subtitle_only_check: Callable[[str, dict], bool],
    ) -> ComposeResult:
        """Run the full compose pipeline and return structured compose output."""
        live_task = _with_live_hot_follow_subtitle_currentness(task_id, task)
        inputs = self._validate_inputs(task_id, live_task, subtitle_only_check)

        compose_started_at = task.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat()

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = self._prepare_workspace(task_id, live_task, inputs, Path(tmpdir), subtitle_resolver)

            # Dispatch to the correct compose branch
            preserve_source = inputs.source_audio_policy == "preserve" and inputs.source_audio_available
            if inputs.subtitle_only_compose:
                self._compose_subtitle_only(ws, inputs)
            elif preserve_source and ws.bgm_path and ws.bgm_path.exists():
                self._compose_voice_source_audio_bgm(ws, inputs)
            elif preserve_source:
                self._compose_voice_source_audio(ws, inputs)
            elif ws.bgm_path and ws.bgm_path.exists():
                self._compose_voice_bgm(ws, inputs)
            else:
                self._compose_voice_only(ws, inputs)

            # Post-process: validate, probe, clamp, upload
            final_path, final_size, final_duration, clamp_warning = (
                self._validate_and_probe_output(task_id, ws, inputs)
            )
            if clamp_warning:
                ws.compose_warning = clamp_warning

            result = self._upload_and_verify(
                task_id,
                task,
                final_path,
                ws=ws,
                final_size=final_size,
                final_duration=final_duration,
                compose_started_at=compose_started_at,
                compose_policy=ws.compose_policy,
                freeze_tail_cap_sec=inputs.freeze_tail_cap_sec,
                compose_warning=ws.compose_warning,
                ffmpeg_cmd_used=ws.ffmpeg_cmd_used,
            )
            if isinstance(result, ComposeResult):
                return result
            updates = dict(result or {})
            final_key = str(
                updates.get("final_video_key")
                or updates.get("final_video_path")
                or deliver_key(task_id, "final.mp4")
            )
            return ComposeResult(
                updates=updates,
                final_key=final_key,
                final_url=task_endpoint(task_id, "final"),
                compose_status=str(updates.get("compose_status") or "done"),
            )

    def execute_hot_follow_compose_contract(
        self,
        task_id: str,
        task: dict,
        request: HotFollowComposeRequestContract,
        *,
        repo,
        hub_loader: Callable[[str, Any], dict[str, Any]],
        subtitle_resolver: Callable[[dict, str, str], str | None],
        subtitle_only_check: Callable[[str, dict], bool],
        revision_snapshot: Callable[[dict], dict[str, str | None]] | None = None,
        lipsync_runner: Callable[[str, bool], str | None] | None = None,
        object_exists_fn: Callable[[str], bool] | None = None,
    ) -> HotFollowComposeResponseContract:
        """Own Hot Follow compose startup, state writes, locking, and finalize.

        Routers call this method as the compose action port. Compose-related
        state transitions must remain behind _write_compose_state() so start,
        success, failure, stale recovery, and lock release have one owner.
        """
        revision_snapshot = revision_snapshot or (lambda current_task: {})
        lipsync_runner = lipsync_runner or (lambda _task_id, _enabled: None)

        current = repo.get(task_id) or task
        line_binding = get_line_runtime_binding(current)
        self.validate_expected_revision(current, request, revision_snapshot=revision_snapshot)

        lock = task_compose_lock(task_id)
        object_exists_for_recovery = object_exists_fn or object_exists
        recovery_updates = self.recover_stale_running_compose(
            task_id,
            current,
            lock_active=lock.locked(),
            object_exists_fn=object_exists_for_recovery,
        )
        if recovery_updates:
            self._write_compose_state(
                repo,
                task_id,
                recovery_updates,
                task=current,
                transition="stale_running_recovered",
                force=True,
            )
            current = repo.get(task_id) or {**current, **recovery_updates}

        if self.compose_lock_active(current):
            self._write_compose_state(
                repo,
                task_id,
                self.build_compose_lock_updates(current),
                task=current,
                transition="lock_conflict",
            )
            return HotFollowComposeResponseContract(
                status_code=409,
                body=self.build_compose_lock_body(task_id),
            )

        if not lock.acquire(blocking=False):
            current = repo.get(task_id) or current
            self._write_compose_state(
                repo,
                task_id,
                self.build_compose_lock_updates(current),
                task=current,
                transition="mutex_conflict",
            )
            return HotFollowComposeResponseContract(
                status_code=409,
                body=self.build_compose_lock_body(task_id),
            )

        lock_acquired = True
        try:
            current_for_plan, request_updates, compose_plan = self.prepare_hot_follow_compose_task(current, request)
            if request_updates:
                self._write_compose_state(
                    repo,
                    task_id,
                    request_updates,
                    task=current,
                    transition="request_prepared",
                )
                current_for_plan = repo.get(task_id) or current_for_plan

            fresh_final_key = self.resolve_fresh_final_key(
                task_id,
                current_for_plan,
                request=request,
                revision_snapshot=revision_snapshot,
            )
            if fresh_final_key:
                latest = repo.get(task_id) or current_for_plan
                return self.build_hot_follow_compose_response(
                    task_id,
                    final_key=fresh_final_key,
                    compose_status=latest.get("compose_status"),
                    hub=hub_loader(task_id, repo),
                    line=line_binding.to_payload(),
                )

            lock_until = (datetime.now(timezone.utc) + timedelta(seconds=300)).isoformat()
            self._write_compose_state(
                repo,
                task_id,
                {"compose_lock_until": lock_until},
                task=current_for_plan,
                transition="lock_acquired",
            )
            running_updates = self.build_compose_running_updates(current_for_plan, compose_plan)
            self._write_compose_state(
                repo,
                task_id,
                running_updates,
                task=current_for_plan,
                transition="running",
            )
            current_for_compose = repo.get(task_id) or {**current_for_plan, **running_updates}

            env_lipsync_enabled = str(os.getenv("HF_LIPSYNC_ENABLED", "0")).strip().lower() in ("1", "true", "yes")
            lipsync_warning = lipsync_runner(task_id, env_lipsync_enabled)
            if lipsync_warning:
                self._write_compose_state(
                    repo,
                    task_id,
                    {"compose_warning": lipsync_warning},
                    task=current_for_compose,
                    transition="lipsync_warning",
                )

            compose_result = self.compose(
                task_id,
                current_for_compose,
                subtitle_resolver=subtitle_resolver,
                subtitle_only_check=subtitle_only_check,
            )
            success_updates = self.merge_compose_warning(compose_result.updates, lipsync_warning)
            self._write_compose_state(
                repo,
                task_id,
                success_updates,
                task=current_for_compose,
                transition="done",
                force=True,
            )
            latest = repo.get(task_id) or {**current_for_compose, **success_updates}
            return self.build_hot_follow_compose_response(
                task_id,
                final_key=compose_result.final_key,
                compose_status=latest.get("compose_status"),
                hub=hub_loader(task_id, repo),
                line=line_binding.to_payload(),
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"reason": "compose_failed", "message": str(exc.detail)}
            self._write_compose_state(
                repo,
                task_id,
                self.build_compose_failure_updates(detail),
                task=repo.get(task_id) or current,
                transition=str(detail.get("reason") or "failed"),
                force=True,
            )
            raise
        except Exception as exc:
            detail = {"reason": "compose_failed", "message": str(exc)}
            self._write_compose_state(
                repo,
                task_id,
                self.build_compose_failure_updates(detail),
                task=repo.get(task_id) or current,
                transition="failed",
                force=True,
            )
            raise HTTPException(status_code=409, detail=detail) from exc
        finally:
            try:
                self._write_compose_state(
                    repo,
                    task_id,
                    {"compose_lock_until": None},
                    task=repo.get(task_id) or current,
                    transition="lock_released",
                    force=True,
                )
            finally:
                if lock_acquired:
                    lock.release()

    @staticmethod
    def _write_compose_state(
        repo,
        task_id: str,
        updates: dict[str, Any],
        *,
        task: dict | None = None,
        transition: str,
        force: bool = False,
    ) -> dict[str, Any]:
        return policy_upsert(
            repo,
            task_id,
            task,
            updates,
            step=f"compose.owner.{transition}",
            force=force,
        )

    def prepare_hot_follow_compose_task(
        self,
        task: dict,
        request: HotFollowComposeRequestContract,
    ) -> tuple[dict[str, Any], dict[str, Any], ComposePlan]:
        current = dict(task or {})
        request_updates: dict[str, Any] = {}
        if request.bgm_mix is not None:
            mix = max(0.0, min(1.0, float(request.bgm_mix)))
            config = dict(current.get("config") or {})
            bgm = dict(config.get("bgm") or {})
            bgm["mix_ratio"] = mix
            config["bgm"] = bgm
            current["config"] = config
            request_updates["config"] = config

        plan_patch: dict[str, Any] = {}
        if request.overlay_subtitles is not None:
            plan_patch["overlay_subtitles"] = bool(request.overlay_subtitles)
        if request.freeze_tail_enabled is not None:
            plan_patch["freeze_tail_enabled"] = bool(request.freeze_tail_enabled)
        if plan_patch:
            plan = dict(current.get("compose_plan") or {})
            if "target_lang" not in plan:
                plan["target_lang"] = current.get("target_lang") or current.get("content_lang") or "mm"
            if "freeze_tail_cap_sec" not in plan:
                plan["freeze_tail_cap_sec"] = 8
            plan.update(plan_patch)
            plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
            current["compose_plan"] = plan
            request_updates["compose_plan"] = plan
        compose_plan = self._build_compose_plan(current)
        return current, request_updates, compose_plan

    def _build_compose_plan(self, task: dict) -> ComposePlan:
        current_plan = dict(task.get("compose_plan") or {})
        freeze_tail_enabled = bool(current_plan.get("freeze_tail_enabled", False))
        return ComposePlan(
            mute=bool(current_plan.get("mute", True)),
            overlay_subtitles=bool(current_plan.get("overlay_subtitles", True)),
            strip_subtitle_streams=bool(current_plan.get("strip_subtitle_streams", True)),
            cleanup_mode=str(current_plan.get("cleanup_mode") or "none"),
            target_lang=str(
                current_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang") or "mm"
            ),
            freeze_tail_enabled=freeze_tail_enabled,
            freeze_tail_cap_sec=int(current_plan.get("freeze_tail_cap_sec") or 8),
            compose_policy="freeze_tail" if freeze_tail_enabled else "match_video",
        )

    @staticmethod
    def compose_lock_active(task: dict) -> bool:
        compose_lock_until = task.get("compose_lock_until")
        if not compose_lock_until:
            return False
        try:
            lock_dt = (
                datetime.fromisoformat(str(compose_lock_until))
                if isinstance(compose_lock_until, str)
                else compose_lock_until
            )
            if lock_dt.tzinfo is None:
                lock_dt = lock_dt.replace(tzinfo=timezone.utc)
            return lock_dt > datetime.now(timezone.utc)
        except Exception:
            return False

    @staticmethod
    def build_compose_running_updates(task: dict, compose_plan: ComposePlan) -> dict[str, Any]:
        return {
            "status": "processing",
            "last_step": "compose",
            "compose_status": "running",
            "compose_error": None,
            "compose_error_reason": None,
            "compose_last_status": "running",
            "compose_last_started_at": datetime.now(timezone.utc).isoformat(),
            "compose_last_finished_at": None,
            "compose_last_error": None,
            "compose_warning": None,
            "compose_plan": compose_plan.to_dict(),
            "scene_outputs": task.get("scene_outputs") or [],
        }

    @staticmethod
    def build_compose_lock_updates(task: dict) -> dict[str, Any]:
        return {
            "compose_status": "running",
            "compose_last_status": "running",
            "compose_last_started_at": task.get("compose_last_started_at")
            or datetime.now(timezone.utc).isoformat(),
            "compose_last_finished_at": None,
        }

    @staticmethod
    def build_compose_lock_body(task_id: str) -> dict[str, Any]:
        return {
            "error": "compose_in_progress",
            "status": "running",
            "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
            "task_id": task_id,
        }

    def resolve_fresh_final_key(
        self,
        task_id: str,
        task: dict,
        *,
        request: HotFollowComposeRequestContract,
        revision_snapshot: Callable[[dict], dict[str, str | None]],
        object_exists_fn: Callable[[str], bool] = object_exists,
        object_head_fn: Callable[[str], dict | None] = object_head,
        media_meta_from_head_fn: Callable[[dict | None], tuple[int, str | None]] = media_meta_from_head,
    ) -> str | None:
        final_key = (
            task_key(task, "final_video_key")
            or task_key(task, "final_video_path")
            or deliver_key(task_id, "final.mp4")
        )
        final_meta = object_head_fn(str(final_key)) if final_key else None
        final_size, _ = media_meta_from_head_fn(final_meta)
        final_physically_exists = bool(
            final_key and object_exists_fn(str(final_key)) and final_size >= MIN_VIDEO_BYTES
        )
        if not final_physically_exists or request.force:
            return None
        revision_for_freshness = revision_snapshot(task)
        if _current_final_is_fresh(
            task,
            revision=revision_for_freshness,
            final_exists=True,
            final_size=final_size,
        ):
            return str(final_key)
        return None

    @staticmethod
    def recover_stale_running_compose(
        task_id: str,
        task: dict,
        *,
        lock_active: bool,
        object_exists_fn: Callable[[str], bool] = object_exists,
        now: datetime | None = None,
        stale_after_sec: int | None = None,
    ) -> dict[str, Any] | None:
        status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip().lower()
        if status not in {"running", "processing", "queued"}:
            return None
        if lock_active:
            return None
        final_key = (
            task_key(task, "final_video_key")
            or task_key(task, "final_video_path")
            or deliver_key(task_id, "final.mp4")
        )
        if final_key and object_exists_fn(str(final_key)):
            return None
        started_raw = str(task.get("compose_last_started_at") or "").strip()
        if not started_raw:
            return None
        try:
            started_at = datetime.fromisoformat(started_raw)
        except ValueError:
            started_at = None
        if started_at is None:
            return None
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        current_time = now or datetime.now(timezone.utc)
        threshold = stale_after_sec
        if threshold is None:
            try:
                threshold = int(os.getenv("HF_COMPOSE_STALE_RUNNING_SEC", "120"))
            except Exception:
                threshold = 120
        if (current_time - started_at).total_seconds() < max(0, int(threshold)):
            return None
        detail = {
            "reason": "compose_stale_running_recovered",
            "message": "Previous compose attempt was running without a live worker or final artifact.",
        }
        updates = CompositionService.build_compose_failure_updates(detail)
        updates["compose_lock_until"] = None
        return updates

    @staticmethod
    def build_compose_failure_updates(detail: dict[str, Any]) -> dict[str, Any]:
        reason = str(detail.get("reason") or "").strip()
        updates = {
            "compose_status": "failed",
            "compose_error": detail,
            "compose_error_reason": detail.get("reason"),
            "compose_last_status": "failed",
            "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
            "compose_last_error": detail.get("message"),
            "status": "failed",
            "last_step": "compose",
            "final_video_key": None,
            "final_video_path": None,
        }
        if reason == "compose_input_derive_failed":
            failure_code = str(detail.get("failure_code") or reason).strip() or reason
            updates["compose_input_policy"] = {
                "mode": "derive_failed",
                "source": "derived_safe",
                "profile": dict(detail.get("compose_input_profile") or {}),
                "safe_key": detail.get("safe_key"),
                "reason": str(detail.get("message") or reason).strip() or reason,
                "failure_code": failure_code,
            }
        elif reason == "compose_input_blocked":
            updates["compose_input_policy"] = {
                "mode": "blocked",
                "source": "raw",
                "profile": dict(detail.get("compose_input_profile") or {}),
                "safe_key": detail.get("safe_key"),
                "reason": str(detail.get("message") or reason).strip() or reason,
                "failure_code": str(detail.get("failure_code") or reason).strip() or reason,
            }
        return updates

    @staticmethod
    def merge_compose_warning(
        updates: dict[str, Any],
        lipsync_warning: str | None,
    ) -> dict[str, Any]:
        merged = dict(updates or {})
        if lipsync_warning:
            current_warning = str(merged.get("compose_warning") or "").strip()
            merged["compose_warning"] = (
                f"{current_warning} {lipsync_warning}".strip() if current_warning else lipsync_warning
            )
        return merged

    @staticmethod
    def build_hot_follow_compose_response(
        task_id: str,
        *,
        final_key: str,
        compose_status: str | None,
        hub: dict[str, Any],
        line: dict[str, Any] | None = None,
    ) -> HotFollowComposeResponseContract:
        return HotFollowComposeResponseContract(
            status_code=200,
            body={
                "task_id": task_id,
                "final_url": task_endpoint(task_id, "final"),
                "final_video_url": task_endpoint(task_id, "final"),
                "final_key": str(final_key or ""),
                "hub": hub,
                "line": dict(line or {}),
                "compose_status": compose_status,
            },
        )

    def validate_expected_revision(
        self,
        task: dict,
        request: HotFollowComposeRequestContract,
        *,
        revision_snapshot: Callable[[dict], dict[str, str | None]],
    ) -> None:
        revision = revision_snapshot(task)
        expected_subtitle_updated_at = str(request.expected_subtitle_updated_at or "").strip() or None
        expected_audio_sha256 = str(request.expected_audio_sha256 or "").strip() or None
        subtitle_mismatch = bool(
            expected_subtitle_updated_at and expected_subtitle_updated_at != revision.get("subtitle_updated_at")
        )
        audio_mismatch = bool(expected_audio_sha256 and expected_audio_sha256 != revision.get("audio_sha256"))
        if subtitle_mismatch or audio_mismatch:
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": "compose_revision_mismatch",
                    "message": "Current subtitles or audio changed; refresh workbench state before composing again.",
                    "current_revision": revision,
                },
            )

    # ── Phase 1: Validation ───────────────────────────────────────────────

    def _validate_inputs(
        self,
        task_id: str,
        task: dict,
        subtitle_only_check: Callable[[str, dict], bool],
    ) -> _ComposeInputs:
        live_task = _with_live_hot_follow_subtitle_currentness(task_id, task)
        voice_state = collect_voice_execution_state(live_task, self._settings)
        subtitle_only_compose = subtitle_only_check(task_id, live_task)

        # Resolve artifact keys
        source_audio_policy = source_audio_policy_from_task(live_task)
        video_key, video_has_source_audio = _resolve_compose_video_key(live_task, source_audio_policy)
        audio_key = _resolve_compose_voiceover_key(live_task, voice_state)

        if not video_key:
            compose_fail("missing_raw", "missing video source for compose")
        if not audio_key and not subtitle_only_compose:
            compose_fail("missing_voiceover", "missing voiceover audio for compose")
        if not bool(voice_state.get("audio_ready")) and not subtitle_only_compose:
            compose_fail(
                "missing_voiceover",
                f"voiceover audio not ready: {voice_state.get('audio_ready_reason') or 'audio_not_ready'}",
            )

        # Validate artifacts in storage
        try:
            assert_artifact_ready(kind="video", key=str(video_key), exists_fn=object_exists, head_fn=object_head)
        except Exception:
            compose_fail("missing_raw", "video source not ready")
        if audio_key and not subtitle_only_compose:
            try:
                assert_artifact_ready(kind="audio", key=str(audio_key), exists_fn=object_exists, head_fn=object_head)
            except Exception:
                compose_fail("missing_voiceover", "voiceover audio invalid")

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            compose_fail("compose_failed", "ffmpeg not found in PATH")

        # Extract compose plan config
        config = dict(live_task.get("config") or {})
        bgm = dict(config.get("bgm") or {})
        bgm_key: str | None = str(bgm.get("bgm_key") or "").strip() or None
        if bgm_key and not object_exists(bgm_key):
            bgm_key = None
        if bgm_key:
            try:
                assert_artifact_ready(kind="audio", key=bgm_key, exists_fn=object_exists, head_fn=object_head)
            except Exception:
                bgm_key = None
        try:
            bgm_mix = float(bgm.get("mix_ratio") if bgm.get("mix_ratio") is not None else 0.3)
        except Exception:
            bgm_mix = 0.3
        bgm_mix = max(0.0, min(1.0, bgm_mix))
        source_has_audio_hint = parse_pipeline_config(live_task.get("pipeline_config")).get("has_audio")
        source_audio_available = bool(
            video_has_source_audio
            and str(source_has_audio_hint or "").strip().lower() != "false"
        )

        compose_plan = dict(live_task.get("compose_plan") or {})
        overlay_subtitles = bool(compose_plan.get("overlay_subtitles"))
        strip_subtitle_streams = bool(compose_plan.get("strip_subtitle_streams", True))
        cleanup_mode = str(compose_plan.get("cleanup_mode") or "none").strip().lower()
        target_lang = str(
            compose_plan.get("target_lang") or live_task.get("target_lang") or live_task.get("content_lang") or "mm"
        )
        freeze_tail_enabled = bool(compose_plan.get("freeze_tail_enabled", False))
        try:
            freeze_tail_cap_sec = max(1.0, min(30.0, float(compose_plan.get("freeze_tail_cap_sec") or 8.0)))
        except Exception:
            freeze_tail_cap_sec = 8.0
        compose_policy = "freeze_tail" if freeze_tail_enabled else "match_video"

        logger.info(
            "COMPOSE_START",
            extra={
                "task_id": task_id,
                "raw_key": str(video_key),
                "audio_key": str(audio_key),
                "bgm_key": str(bgm_key) if bgm_key else None,
                "mix": bgm_mix,
                "source_audio_input_key": str(video_key) if source_audio_available else None,
                "source_audio_mix": _source_audio_bed_volume(bgm_mix) if source_audio_available else None,
                "video_has_source_audio": bool(video_has_source_audio),
                "source_audio_policy": source_audio_policy,
                "source_audio_available": source_audio_available,
                "overlay_subtitles": overlay_subtitles,
                "strip_subtitle_streams": strip_subtitle_streams,
                "target_lang": target_lang,
                "freeze_tail_enabled": freeze_tail_enabled,
                "freeze_tail_cap_sec": freeze_tail_cap_sec,
                "compose_policy": compose_policy,
            },
        )

        return _ComposeInputs(
            video_key=str(video_key),
            audio_key=str(audio_key) if audio_key else None,
            subtitle_only_compose=subtitle_only_compose,
            voice_state=voice_state,
            bgm_key=bgm_key,
            bgm_mix=bgm_mix,
            source_audio_policy=source_audio_policy,
            source_audio_available=source_audio_available,
            overlay_subtitles=overlay_subtitles,
            strip_subtitle_streams=strip_subtitle_streams,
            cleanup_mode=cleanup_mode,
            target_lang=target_lang,
            freeze_tail_enabled=freeze_tail_enabled,
            freeze_tail_cap_sec=freeze_tail_cap_sec,
            compose_policy=compose_policy,
            ffmpeg=str(ffmpeg),
        )

    # ── Phase 2: Workspace preparation ────────────────────────────────────

    def _prepare_workspace(
        self,
        task_id: str,
        task: dict,
        inputs: _ComposeInputs,
        tmp: Path,
        subtitle_resolver: Callable[[dict, str, str], str | None],
    ) -> _WorkspaceFiles:
        video_path = tmp / "video_input.mp4"
        voice_path = tmp / "voice_input.mp3"
        final_path = tmp / "final_compose.mp4"
        subtitle_path = tmp / "subs_target.srt"

        self._storage.download_file(inputs.video_key, str(video_path))
        if inputs.audio_key and not inputs.subtitle_only_compose:
            self._storage.download_file(inputs.audio_key, str(voice_path))

        video_size, video_duration = assert_local_video_ok(video_path)
        input_profile = self._probe_video_profile(task_id, video_path, video_size, video_duration)
        self._guard_workdir_space(task_id, tmp, input_profile)
        video_path, input_profile, derive_warning = self._derive_safe_compose_input(
            task_id,
            task,
            inputs,
            video_path,
            tmp,
            input_profile,
        )
        video_size, video_duration = assert_local_video_ok(video_path)
        voice_duration = 0.0
        if inputs.audio_key and not inputs.subtitle_only_compose:
            try:
                _, voice_duration = assert_local_audio_ok(voice_path)
            except ValueError:
                compose_fail("missing_voiceover", "voiceover audio invalid")

        video_input_path = video_path
        compose_policy = inputs.compose_policy
        compose_warning: str | None = derive_warning

        # ── Freeze-tail ──
        hold_sec = 0.0
        if inputs.freeze_tail_enabled and voice_duration > video_duration:
            required_hold = max(0.0, voice_duration - video_duration)
            if required_hold <= inputs.freeze_tail_cap_sec:
                hold_sec = required_hold
            else:
                compose_policy = "match_video"
                compose_warning = (
                    f"freeze tail required {required_hold:.2f}s > cap {inputs.freeze_tail_cap_sec:.2f}s; "
                    "fallback to match_video"
                )
        else:
            compose_policy = "match_video" if not inputs.freeze_tail_enabled else compose_policy

        if hold_sec > 0:
            result_path = self._apply_freeze_tail(task_id, inputs.ffmpeg, video_path, tmp, hold_sec)
            if result_path:
                video_input_path = result_path
                try:
                    _, video_duration = assert_local_video_ok(result_path)
                except ValueError:
                    video_duration = video_duration + hold_sec
                compose_policy = "freeze_tail"
            else:
                compose_policy = "match_video"
                compose_warning = "freeze tail render failed; fallback to match_video"

        # ── Subtitle download & validation ──
        bundled_fonts_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
        bundled_myanmar_ttf = bundled_fonts_dir / "NotoSansMyanmar-Regular.ttf"
        overlay_subtitles = inputs.overlay_subtitles
        requested_overlay_subtitles = overlay_subtitles
        subtitle_key_used: str | None = None
        subtitle_object_etag: str | None = None
        subtitle_content_hash: str | None = None
        subtitle_sha256: str | None = None

        if overlay_subtitles:
            subtitle_key = subtitle_resolver(task, task_id, inputs.target_lang)
            if not subtitle_key:
                if inputs.subtitle_only_compose:
                    overlay_subtitles = False
                else:
                    compose_fail("subtitles_missing", "overlay_subtitles enabled but target subtitle key is missing")
            if overlay_subtitles and (not bundled_myanmar_ttf.exists() or bundled_myanmar_ttf.stat().st_size == 0):
                compose_fail("font_missing", f"bundled Myanmar font missing: {bundled_myanmar_ttf}")
            subtitle_key_used = str(subtitle_key) if subtitle_key else None
        if overlay_subtitles and subtitle_key_used:
            subtitle_meta = object_head(subtitle_key_used)
            subtitle_object_etag = (
                str(subtitle_meta.get("etag") or "").strip() or None
                if isinstance(subtitle_meta, dict)
                else None
            )
            self._storage.download_file(subtitle_key_used, str(subtitle_path))
            if not subtitle_path.exists() or subtitle_path.stat().st_size == 0:
                if inputs.subtitle_only_compose:
                    # Historical fix (267744a): no-speech task with empty subtitle —
                    # skip overlay, compose succeeds without burned-in text.
                    overlay_subtitles = False
                else:
                    compose_fail("subtitles_missing", "overlay_subtitles enabled but subtitle file is empty")
            if overlay_subtitles:
                subtitle_text = _read_text_compat(subtitle_path)
                subtitle_content_hash = _subtitle_content_hash(subtitle_text)
                subtitle_sha256 = sha256_file(subtitle_path)
                expected_subtitle_hash = str(task.get("subtitles_content_hash") or "").strip() or None
                logger.info(
                    "COMPOSE_SUBTITLE_BOUND",
                    extra={
                        "task_id": task_id,
                        "subtitle_key": subtitle_key_used,
                        "subtitle_etag": subtitle_object_etag,
                        "expected_subtitle_hash": expected_subtitle_hash,
                        "downloaded_subtitle_hash": subtitle_content_hash,
                    },
                )
                if expected_subtitle_hash and subtitle_content_hash and expected_subtitle_hash != subtitle_content_hash:
                    compose_fail(
                        "subtitle_revision_mismatch",
                        (
                            "downloaded authoritative subtitle does not match current saved subtitle "
                            f"(expected {expected_subtitle_hash}, got {subtitle_content_hash})"
                        ),
                    )
                normalized_layout_text = optimize_hot_follow_subtitle_layout_srt(
                    subtitle_text,
                    inputs.target_lang,
                )
                if normalized_layout_text and normalized_layout_text != subtitle_text:
                    subtitle_path.write_text(normalized_layout_text, encoding="utf-8")

        # ── BGM download ──
        bgm_path: Path | None = None
        if inputs.bgm_key:
            bgm_path = tmp / "bgm_input.mp3"
            self._storage.download_file(str(inputs.bgm_key), str(bgm_path))

        compose_input_policy = dict(task.get("compose_input_policy") or {})
        media_policy = hot_follow_media_input_policy()
        if derive_warning:
            compose_input_policy.update(
                {
                    "mode": "derived_ready",
                    "source": "derived_safe",
                    "profile": input_profile.to_dict(),
                    "safe_key": video_path.name,
                    "reason": "large_local_input_derived",
                    "failure_code": None,
                    "quality_tier_default": media_policy.quality_tier_default,
                    "target_output_band": media_policy.target_output_band,
                    "prefer_source_quality_preservation": media_policy.prefer_source_quality_preservation,
                }
            )
        elif str(compose_input_policy.get("mode") or "").strip().lower() not in {"blocked", "derive_failed"}:
            compose_input_policy.update(
                {
                    "mode": "direct",
                    "source": compose_input_policy.get("source") or "raw",
                    "profile": input_profile.to_dict(),
                    "safe_key": video_path.name,
                    "reason": compose_input_policy.get("reason"),
                    "failure_code": None,
                    "quality_tier_default": media_policy.quality_tier_default,
                    "target_output_band": media_policy.target_output_band,
                    "prefer_source_quality_preservation": media_policy.prefer_source_quality_preservation,
                }
            )

        if requested_overlay_subtitles and not overlay_subtitles and not compose_warning:
            compose_warning = "subtitle_overlay_skipped_empty_no_dub"

        return _WorkspaceFiles(
            task_id=task_id,
            tmp=tmp,
            video_input_path=video_input_path,
            voice_path=voice_path if (inputs.audio_key and not inputs.subtitle_only_compose) else None,
            final_path=final_path,
            subtitle_path=subtitle_path if overlay_subtitles else None,
            bgm_path=bgm_path,
            fontsdir=bundled_fonts_dir,
            ffmpeg=inputs.ffmpeg,
            video_duration=video_duration,
            voice_duration=voice_duration,
            compose_policy=compose_policy,
            subtitle_key=subtitle_key_used,
            subtitle_object_etag=subtitle_object_etag,
            subtitle_content_hash=subtitle_content_hash,
            subtitle_sha256=subtitle_sha256,
            compose_warning=compose_warning,
            overlay_subtitles=overlay_subtitles,
            compose_input_policy=compose_input_policy,
        )

    def _apply_freeze_tail(
        self,
        task_id: str,
        ffmpeg: str,
        video_path: Path,
        tmp: Path,
        hold_sec: float,
    ) -> Path | None:
        """Apply tpad freeze-tail.  Returns new path on success, None on failure."""
        freeze_video_path = tmp / "video_input_freeze_tail.mp4"
        freeze_cmd = [
            ffmpeg, "-y", "-i", str(video_path),
            "-vf", f"tpad=stop_mode=clone:stop_duration={hold_sec:.3f}",
            "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p",
            str(freeze_video_path),
        ]
        try:
            proc = self._run_ffmpeg(freeze_cmd, task_id, "freeze_tail", timeout=self._timeouts.freeze_tail)
        except HTTPException:
            # Timeout or failure — caller will fallback to match_video
            return None
        if proc.returncode == 0 and freeze_video_path.exists() and freeze_video_path.stat().st_size > 0:
            return freeze_video_path
        return None

    # ── Phase 3: FFmpeg execution ─────────────────────────────────────────

    def _run_ffmpeg(
        self,
        cmd: list[str],
        task_id: str,
        purpose: str,
        *,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess:
        """Unified subprocess gateway with timeout protection."""
        effective_timeout = timeout or self._timeouts.compose
        logger.info(
            "COMPOSE_SUBPROCESS_START task=%s purpose=%s timeout=%d",
            task_id,
            purpose,
            effective_timeout,
        )
        binding = get_line_runtime_binding({"kind": "hot_follow"})
        line = binding.line
        request = WorkerRequest(
            request_id=f"{task_id}:{purpose}",
            line_id=str(getattr(line, "line_id", None) or "hot_follow_line"),
            task_id=task_id,
            step_id="compose",
            worker_capability="ffmpeg",
            execution_mode=WorkerExecutionMode.INTERNAL,
            worker_profile_ref=getattr(line, "worker_profile_ref", None),
            input_refs={"task_ref": task_id},
            strategy_hints={"purpose": purpose},
            runtime_config={"timeout_seconds": effective_timeout},
            payload={"cmd": list(cmd)},
        )
        result = get_worker_gateway().execute(request)
        if result.result == "timeout":
            stderr_tail = str((result.raw_output or {}).get("stderr") or "")[-800:]
            compose_fail(
                "compose_timeout",
                f"{purpose} timed out after {effective_timeout}s",
                ffmpeg_cmd=" ".join(cmd),
                stderr_tail=stderr_tail,
            )
        returncode = (result.output_facts or {}).get("returncode")
        if returncode is None:
            returncode = 1
        return subprocess.CompletedProcess(
            list(cmd),
            int(returncode),
            str((result.raw_output or {}).get("stdout") or ""),
            str((result.raw_output or {}).get("stderr") or ""),
        )

    def _probe_video_profile(self, task_id: str, video_path: Path, fallback_size: int, fallback_duration: float) -> ComposeInputProfile:
        profile = ComposeInputProfile(size_bytes=int(fallback_size or 0), duration_sec=float(fallback_duration or 0.0))
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return profile
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,bit_rate,pix_fmt:format=duration,bit_rate",
            "-of",
            "json",
            str(video_path),
        ]
        try:
            proc = self._run_ffmpeg(cmd, task_id, "compose_input_probe", timeout=self._timeouts.probe)
        except HTTPException:
            return profile
        if proc.returncode != 0:
            return profile
        try:
            data = json.loads(proc.stdout or "{}")
        except Exception:
            return profile
        streams = data.get("streams") if isinstance(data, dict) else None
        stream = streams[0] if isinstance(streams, list) and streams and isinstance(streams[0], dict) else {}
        fmt = data.get("format") if isinstance(data, dict) and isinstance(data.get("format"), dict) else {}

        def _int(value: Any) -> int | None:
            try:
                parsed = int(float(str(value)))
            except Exception:
                return None
            return parsed if parsed > 0 else None

        def _float(value: Any) -> float | None:
            try:
                parsed = float(str(value))
            except Exception:
                return None
            return parsed if parsed > 0 else None

        return ComposeInputProfile(
            size_bytes=int(fallback_size or 0),
            duration_sec=_float(fmt.get("duration")) or float(fallback_duration or 0.0),
            width=_int(stream.get("width")),
            height=_int(stream.get("height")),
            bit_rate=_int(stream.get("bit_rate")) or _int(fmt.get("bit_rate")),
            pix_fmt=str(stream.get("pix_fmt") or "").strip() or None,
        )

    @staticmethod
    def _large_input_limits() -> dict[str, int]:
        policy = hot_follow_media_input_policy()

        def _env_int(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except Exception:
                return default

        return {
            "bytes": _env_int("HF_COMPOSE_DERIVE_MIN_BYTES", policy.derive_min_bytes),
            "bitrate": policy.derive_min_bitrate,
            "pixels": policy.derive_min_pixels,
            "max_short_edge": policy.target_short_edge_max,
            "max_long_edge": policy.target_long_edge_max,
            "short_edge_floor": policy.target_short_edge_floor,
            "crf": policy.derive_crf,
        }

    @staticmethod
    def _should_derive_safe_compose_input(task: dict, profile: ComposeInputProfile) -> bool:
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        local_upload = str(pipeline_config.get("ingest_mode") or "").strip().lower() == "local"
        if not local_upload and str(task.get("source_url") or "").strip():
            return False
        limits = CompositionService._large_input_limits()
        return bool(
            int(profile.size_bytes or 0) >= limits["bytes"]
            or int(profile.bit_rate or 0) >= limits["bitrate"]
            or int(profile.pixels or 0) > limits["pixels"]
        )

    def _guard_workdir_space(self, task_id: str, tmp: Path, profile: ComposeInputProfile, *, multiplier: float = 3.0) -> None:
        usage = shutil.disk_usage(tmp)
        required = max(
            512 * 1024 * 1024,
            int((profile.size_bytes or 0) * multiplier),
            int((profile.bit_rate or 0) * max(profile.duration_sec or 0.0, 1.0) / 8 * 1.5),
        )
        if usage.free < required:
            compose_fail(
                "compose_insufficient_disk",
                f"compose workspace has {usage.free} bytes free, requires at least {required} bytes",
                status_code=507,
            )
        logger.info(
            "COMPOSE_WORKDIR_GUARD",
            extra={"task_id": task_id, "free_bytes": usage.free, "required_bytes": required},
        )

    def _derive_safe_compose_input(
        self,
        task_id: str,
        task: dict,
        inputs: _ComposeInputs,
        video_path: Path,
        tmp: Path,
        profile: ComposeInputProfile,
    ) -> tuple[Path, ComposeInputProfile, str | None]:
        self._guard_workdir_space(task_id, tmp, profile, multiplier=4.0)
        if not self._should_derive_safe_compose_input(task, profile):
            return video_path, profile, None

        limits = self._large_input_limits()
        media_policy = hot_follow_media_input_policy()
        safe_path = tmp / "video_input_safe.mp4"
        scale_expr = hot_follow_compose_scale_expr(media_policy)
        cmd = [
            inputs.ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            scale_expr,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(limits["crf"]),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-map_metadata",
            "-1",
            "-movflags",
            "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(safe_path),
        ]
        proc = self._run_ffmpeg(cmd, task_id, "derive_compose_input", timeout=self._timeouts.derive)
        if proc.returncode != 0 or not safe_path.exists() or safe_path.stat().st_size == 0:
            compose_fail(
                "compose_input_derive_failed",
                "failed to derive safe compose input",
                ffmpeg_cmd=" ".join(cmd),
                stderr_tail=(proc.stderr or "")[-800:],
                extra={
                    "failure_code": "derive_ffmpeg_failed",
                    "compose_input_profile": profile.to_dict(),
                    "safe_key": safe_path.name,
                    "quality_tier_default": media_policy.quality_tier_default,
                    "target_output_band": media_policy.target_output_band,
                },
            )
        safe_size, safe_duration = assert_local_video_ok(safe_path)
        safe_profile = self._probe_video_profile(task_id, safe_path, safe_size, safe_duration)
        derived_width = int(safe_profile.width or 0)
        derived_height = int(safe_profile.height or 0)
        if (
            derived_width <= 0
            or derived_height <= 0
            or derived_width % 2
            or derived_height % 2
            or str(safe_profile.pix_fmt or "").strip().lower() != "yuv420p"
        ):
            compose_fail(
                "compose_input_derive_failed",
                "derived compose input is not encoder-safe",
                ffmpeg_cmd=" ".join(cmd),
                extra={
                    "failure_code": "derive_not_encoder_safe",
                    "compose_input_profile": profile.to_dict(),
                    "derived_compose_input_profile": safe_profile.to_dict(),
                    "safe_key": safe_path.name,
                    "quality_tier_default": media_policy.quality_tier_default,
                    "target_output_band": media_policy.target_output_band,
                },
            )
        logger.info(
            "COMPOSE_INPUT_DERIVED",
            extra={
                "task_id": task_id,
                "source_size": profile.size_bytes,
                "source_bitrate": profile.bit_rate,
                "source_pixels": profile.pixels,
                "derived_size": safe_profile.size_bytes,
                "derived_bitrate": safe_profile.bit_rate,
                "derived_pixels": safe_profile.pixels,
            },
        )
        return safe_path, safe_profile, "large local input derived for stable compose"

    # ── Filter expression helpers (ex-nested, now methods) ────────────────

    def _bgm_filter_expr(self, bgm_mix: float, compose_policy: str, video_duration: float) -> str:
        base = f"[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={bgm_mix}"
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base + "[bgm];"

    def _bgm_only_filter_expr(self, input_index: int, bgm_mix: float, compose_policy: str, video_duration: float) -> str:
        base = f"[{input_index}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={bgm_mix}"
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base + ",alimiter=limit=0.95[mix]"

    def _source_audio_filter_expr(self, source_audio_mix: float, compose_policy: str, video_duration: float) -> str:
        base = (
            "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume={_source_audio_bed_volume(source_audio_mix):.3f}"
        )
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base

    def _voice_filter_expr(self, ws: _WorkspaceFiles) -> str:
        base = "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
        if ws.compose_policy != "match_video":
            return base
        if ws.voice_duration > ws.video_duration:
            return (
                base
                + f",atrim=0:{ws.video_duration:.3f}"
                + f",afade=t=out:st={max(ws.video_duration - 0.35, 0.0):.3f}:d=0.35"
            )
        return base + f",apad,atrim=0:{ws.video_duration:.3f}"

    @staticmethod
    def _assert_overlay_cmd(cmd_text: str, overlay_subtitles: bool) -> None:
        if overlay_subtitles and "subtitles=" not in cmd_text:
            compose_fail(
                "compose_failed",
                "overlay_subtitles enabled but ffmpeg cmd missing subtitles filter",
                ffmpeg_cmd=cmd_text,
            )

    # ── Compose branches ──────────────────────────────────────────────────

    def _compose_subtitle_only(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: subtitle-only compose (no voice audio)."""
        preserve_source = inputs.source_audio_policy == "preserve" and inputs.source_audio_available
        if preserve_source and ws.bgm_path and ws.bgm_path.exists():
            self._compose_subtitle_only_source_audio_bgm(ws, inputs)
        elif preserve_source:
            self._compose_subtitle_only_source_audio(ws, inputs)
        elif ws.bgm_path and ws.bgm_path.exists():
            self._compose_subtitle_only_with_bgm(ws, inputs)
        else:
            self._compose_subtitle_only_no_bgm(ws, inputs)

    def _compose_subtitle_only_source_audio(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + ",alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration) + ",alimiter=limit=0.95[mix]"
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_source_audio_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        bgm_filter = self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration).removesuffix(",alimiter=limit=0.95[mix]")
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[source][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[source][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_with_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration)
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration)
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_no_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-vf", subtitle_filter,
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "20", "-pix_fmt", "yuv420p",
                "-an",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
        else:
            cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-c:v", "copy",
                "-an",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + BGM compose."""
        voice_filter = self._voice_filter_expr(ws)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + (voice_filter + "[voice];")
                + self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                (voice_filter + "[voice];")
                + self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_source_audio(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + preserved source audio bed."""
        voice_filter = self._voice_filter_expr(ws)
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + "[voice][source]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + "[voice][source]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_source_audio_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + preserved source audio bed + uploaded BGM."""
        voice_filter = self._voice_filter_expr(ws)
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        bgm_filter = self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration).removesuffix("[bgm];")
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[voice][source][bgm]amix=inputs=3:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[voice][source][bgm]amix=inputs=3:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_only(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice without BGM.  Includes CRF23 fallback retry."""
        voice_filter = self._voice_filter_expr(ws)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + (voice_filter + ",alimiter=limit=0.95[mix]")
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = voice_filter + ",alimiter=limit=0.95[mix]"
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]

        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd))
        ws.ffmpeg_cmd_used = " ".join(cmd)
        self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
        proc = self._run_ffmpeg(cmd, ws.task_id, "compose_voice_only")

        if proc.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
            # Fallback: retry with CRF 23
            cmd_fallback = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-i", str(ws.voice_path),
                "-filter_complex", filter_complex,
                "-map", map_video,
                "-map", "[mix]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
            logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd_fallback))
            ws.ffmpeg_cmd_used = " ".join(cmd_fallback)
            self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
            proc2 = self._run_ffmpeg(cmd_fallback, ws.task_id, "compose_voice_only_fallback")
            if proc2.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
                compose_fail(
                    "compose_failed",
                    "compose ffmpeg failed",
                    ffmpeg_cmd=ws.ffmpeg_cmd_used,
                    stderr_tail=(proc2.stderr or "")[-800:],
                )

    def _execute_compose_cmd(self, cmd: list[str], ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Log, assert, run, and check a compose command (shared by non-fallback branches)."""
        logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd))
        ws.ffmpeg_cmd_used = " ".join(cmd)
        self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
        proc = self._run_ffmpeg(cmd, ws.task_id, "compose")
        if proc.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
            compose_fail(
                "compose_failed",
                "compose ffmpeg failed",
                ffmpeg_cmd=ws.ffmpeg_cmd_used,
                stderr_tail=(proc.stderr or "")[-800:],
            )

    # ── Phase 4: Post-process ─────────────────────────────────────────────

    def _validate_and_probe_output(
        self,
        task_id: str,
        ws: _WorkspaceFiles,
        inputs: _ComposeInputs,
    ) -> tuple[Path, int, float, str | None]:
        """Validate output, probe duration, clamp if needed.  Returns (path, size, duration, warning)."""
        try:
            final_size, final_duration = assert_local_video_ok(ws.final_path)
        except ValueError:
            compose_fail("compose_failed", "compose output invalid")
            # compose_fail always raises; this is unreachable but helps type checker
            raise  # pragma: no cover

        # Probe with ffprobe for more accurate duration
        ffprobe = shutil.which("ffprobe")
        if ffprobe:
            probe_cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(ws.final_path),
            ]
            try:
                probe = self._run_ffmpeg(probe_cmd, task_id, "probe_duration", timeout=self._timeouts.probe)
                if probe.returncode == 0:
                    try:
                        final_duration = float((probe.stdout or "").strip() or final_duration)
                    except Exception:
                        pass
            except HTTPException:
                # Probe timeout — non-fatal, use duration from assert_local_video_ok
                pass

        # Duration mismatch clamping
        clamp_warning: str | None = None
        final_path = ws.final_path
        if ws.compose_policy == "match_video" and abs(float(final_duration) - float(ws.video_duration)) > 1.0:
            logger.warning(
                "COMPOSE_DURATION_MISMATCH",
                extra={
                    "task_id": task_id,
                    "source_duration": ws.video_duration,
                    "final_duration": final_duration,
                },
            )
            clamp_path = ws.tmp / "final_compose_clamped.mp4"
            clamp_cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.final_path),
                "-t", f"{ws.video_duration:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac",
                "-movflags", "+faststart",
                str(clamp_path),
            ]
            try:
                clamp_proc = self._run_ffmpeg(clamp_cmd, task_id, "duration_clamp", timeout=self._timeouts.clamp)
                if clamp_proc.returncode == 0 and clamp_path.exists() and clamp_path.stat().st_size > 0:
                    final_path = clamp_path
                    final_size, final_duration = assert_local_video_ok(final_path)
                    clamp_warning = "Duration mismatch detected; output was clamped to source duration."
            except HTTPException:
                # Clamp timeout — non-fatal, keep unclamped version
                clamp_warning = "Duration mismatch detected; clamp timed out, keeping original output."

        logger.info(
            "COMPOSE_OUTPUT_READY",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "output_path": str(final_path),
            },
        )
        return final_path, final_size, final_duration, clamp_warning

    def _upload_and_verify(
        self,
        task_id: str,
        task: dict,
        final_path: Path,
        *,
        ws: _WorkspaceFiles,
        final_size: int,
        final_duration: float,
        compose_started_at: str,
        compose_policy: str,
        freeze_tail_cap_sec: float,
        compose_warning: str | None,
        ffmpeg_cmd_used: str | None,
    ) -> ComposeResult:
        """Upload final video, verify, and build the structured compose result."""
        final_key = deliver_key(task_id, "final.mp4")
        logger.info(
            "COMPOSE_UPLOAD_START",
            extra={"task_id": task_id, "final_key": final_key, "content_type": "video/mp4"},
        )
        uploaded_key = self._storage.upload_file(str(final_path), final_key, content_type="video/mp4")
        if not uploaded_key:
            compose_fail("compose_failed", "compose upload failed")
        if not object_exists(final_key):
            compose_fail("compose_failed", "compose upload verify failed: missing final object")
        uploaded_meta = object_head(final_key)
        uploaded_size, _ = media_meta_from_head(uploaded_meta)
        final_etag = uploaded_meta.get("etag") if isinstance(uploaded_meta, dict) else None
        if uploaded_size < MIN_VIDEO_BYTES:
            compose_fail("compose_failed", "compose upload verify failed: invalid final object")

        logger.info(
            "COMPOSE_DONE",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "uploaded_key": final_key,
                "uploaded_size": uploaded_size,
            },
        )

        compose_finished_at = datetime.now(timezone.utc).isoformat()
        updates = {
            "final_video_key": final_key,
            "final_video_path": final_key,
            "final_video_sha256": sha256_file(final_path),
            "final_asset_version": str(final_etag or sha256_file(final_path) or compose_finished_at),
            "final_updated_at": compose_finished_at,
            "final_mime": "video/mp4",
            "final_duration_ms": int(final_duration * 1000),
            "final_video_bytes": int(uploaded_size),
            # Compose snapshot: record which inputs were baked into this final.
            # Used by _current_final_is_fresh() and compute_final_staleness() to
            # detect when subtitle or audio changed after the last compose ran.
            "final_source_audio_sha256": str(task.get("audio_sha256") or "").strip() or None,
            "final_source_dub_generated_at": str(task.get("dub_generated_at") or "").strip() or None,
            "final_source_audio_policy": source_audio_policy_from_task(task),
            "final_source_subtitles_content_hash": ws.subtitle_content_hash
            or str(task.get("subtitles_content_hash") or "").strip()
            or None,
            "final_source_subtitle_updated_at": str(task.get("subtitles_override_updated_at") or "").strip() or None,
            "final_source_subtitle_storage_key": ws.subtitle_key,
            "final_source_subtitle_storage_etag": ws.subtitle_object_etag,
            "final_source_subtitle_sha256": ws.subtitle_sha256,
            "final_source_render_signature": subtitle_render_signature(
                target_lang=(task.get("compose_plan") or {}).get("target_lang")
                or task.get("target_lang")
                or task.get("content_lang"),
                cleanup_mode=(task.get("compose_plan") or {}).get("cleanup_mode"),
            ),
            "compose_provider": "ffmpeg",
            "compose_version": int(task.get("compose_version") or 0) + 1,
            "compose_status": "done",
            "compose_error": None,
            "compose_error_reason": None,
            "compose_last_status": "done",
            "compose_last_started_at": compose_started_at,
            "compose_last_finished_at": compose_finished_at,
            "compose_last_ffmpeg_cmd": ffmpeg_cmd_used,
            "compose_last_error": None,
            "compose_policy": compose_policy,
            "freeze_tail_enabled": bool(compose_policy == "freeze_tail"),
            "freeze_tail_cap_sec": int(freeze_tail_cap_sec),
            "compose_warning": compose_warning,
            "compose_input_policy": dict(ws.compose_input_policy or {}),
            "compose_output_quality_policy": hot_follow_media_input_policy().to_contract_dict(),
            "last_step": "compose",
            "status": "ready",
            "error_message": None,
            "error_reason": None,
        }
        return ComposeResult(
            updates=updates,
            final_key=final_key,
            final_url=task_endpoint(task_id, "final"),
            compose_status=str(updates.get("compose_status") or "done"),
        )

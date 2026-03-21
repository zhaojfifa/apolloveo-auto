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

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from gateway.app.services.artifact_storage import object_exists, object_head
from gateway.app.services.media_helpers import sha256_file
from gateway.app.services.media_validation import (
    MIN_VIDEO_BYTES,
    assert_artifact_ready,
    assert_local_audio_ok,
    assert_local_video_ok,
    deliver_key,
    media_meta_from_head,
)
from gateway.app.services.voice_state import collect_voice_execution_state
from gateway.app.services.compose_helpers import task_compose_lock
from gateway.app.services.task_view_helpers import task_endpoint, task_key
from gateway.app.core.constants import COMPOSE_RETRY_AFTER_MS

logger = logging.getLogger(__name__)

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
    composed_audio_sha = str(task.get("final_source_audio_sha256") or "").strip() or None
    composed_sub_hash = str(task.get("final_source_subtitles_content_hash") or "").strip() or None
    composed_sub_at = str(task.get("final_source_subtitle_updated_at") or "").strip() or None

    # No compose snapshot → cannot confirm what was baked into the final → recompose.
    if not composed_audio_sha and not composed_sub_hash:
        return False

    if composed_audio_sha and current_audio_sha and composed_audio_sha != current_audio_sha:
        return False
    if composed_sub_hash and current_sub_hash:
        if composed_sub_hash != current_sub_hash:
            return False
    elif composed_sub_at and current_sub_at and composed_sub_at != current_sub_at:
        return False
    return True


def compose_fail(
    reason: str,
    message: str,
    status_code: int = 409,
    *,
    ffmpeg_cmd: str | None = None,
    stderr_tail: str | None = None,
) -> None:
    """Raise HTTPException with structured compose error detail."""
    detail: dict[str, Any] = {"reason": reason, "message": message}
    if ffmpeg_cmd:
        detail["ffmpeg_cmd"] = ffmpeg_cmd
    if stderr_tail:
        detail["stderr_tail"] = stderr_tail
    raise HTTPException(status_code=status_code, detail=detail)


def escape_subtitles_path(path: Path) -> str:
    """Escape a path for use in FFmpeg subtitles filter expressions."""
    raw = str(path).replace("\\", "/")
    return raw.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def source_subtitle_cover_filter(cleanup_mode: str) -> str:
    """Return an FFmpeg drawbox filter for subtitle area masking."""
    mode = str(cleanup_mode or "").strip().lower()
    if mode == "bottom_mask":
        return "drawbox=x=0:y=ih*0.80:w=iw:h=ih*0.20:color=black@0.92:t=fill"
    if mode == "safe_band":
        return "drawbox=x=0:y=ih*0.74:w=iw:h=ih*0.26:color=black@0.96:t=fill"
    return ""


def compose_subtitle_vf(subtitle_path_obj: Path, fontsdir: Path, cleanup_mode: str) -> str:
    """Build the complete subtitle video-filter string for FFmpeg."""
    subtitle_filter = (
        f"subtitles='{escape_subtitles_path(subtitle_path_obj)}':"
        "charenc=UTF-8:"
        f"fontsdir='{escape_subtitles_path(Path(fontsdir))}':"
        "force_style='FontName=Noto Sans Myanmar,FontSize=18,Outline=2,Shadow=1,MarginV=40'"
    )
    cover_filter = source_subtitle_cover_filter(cleanup_mode)
    return f"{cover_filter},{subtitle_filter}" if cover_filter else subtitle_filter


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


@dataclass
class _ComposeInputs:
    """Validated inputs extracted from task dict."""

    video_key: str
    audio_key: str | None
    subtitle_only_compose: bool
    voice_state: dict
    bgm_key: str | None
    bgm_mix: float
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
    compose_warning: str | None = None
    ffmpeg_cmd_used: str | None = None
    overlay_subtitles: bool = True


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
    ) -> dict[str, Any]:
        """Run the full compose pipeline.  Returns the 27-field update dict."""
        inputs = self._validate_inputs(task_id, task, subtitle_only_check)

        compose_started_at = task.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat()

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = self._prepare_workspace(task_id, task, inputs, Path(tmpdir), subtitle_resolver)

            # Dispatch to the correct compose branch
            if inputs.subtitle_only_compose:
                self._compose_subtitle_only(ws, inputs)
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

            return self._upload_and_verify(
                task_id,
                task,
                final_path,
                final_size=final_size,
                final_duration=final_duration,
                compose_started_at=compose_started_at,
                compose_policy=ws.compose_policy,
                freeze_tail_cap_sec=inputs.freeze_tail_cap_sec,
                compose_warning=ws.compose_warning,
                ffmpeg_cmd_used=ws.ffmpeg_cmd_used,
            )

    def _apply_request_mutations(
        self,
        repo: Any,
        task_id: str,
        task: dict,
        request: HotFollowComposeRequestContract,
        policy_upsert: Callable[[Any, str, dict[str, Any]], Any],
    ) -> dict:
        current = task
        if request.bgm_mix is not None:
            mix = max(0.0, min(1.0, float(request.bgm_mix)))
            config = dict(current.get("config") or {})
            bgm = dict(config.get("bgm") or {})
            bgm["mix_ratio"] = mix
            config["bgm"] = bgm
            policy_upsert(repo, task_id, {"config": config})
            current = repo.get(task_id) or current

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
            policy_upsert(repo, task_id, {"compose_plan": plan})
            current = repo.get(task_id) or current
        return current

    def _build_compose_plan(self, task: dict) -> dict[str, Any]:
        current_plan = dict(task.get("compose_plan") or {})
        return {
            "mute": bool(current_plan.get("mute", True)),
            "overlay_subtitles": bool(current_plan.get("overlay_subtitles", True)),
            "strip_subtitle_streams": bool(current_plan.get("strip_subtitle_streams", True)),
            "cleanup_mode": str(current_plan.get("cleanup_mode") or "none"),
            "target_lang": str(
                current_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang") or "mm"
            ),
            "freeze_tail_enabled": bool(current_plan.get("freeze_tail_enabled", False)),
            "freeze_tail_cap_sec": int(current_plan.get("freeze_tail_cap_sec") or 8),
            "compose_policy": "freeze_tail"
            if bool(current_plan.get("freeze_tail_enabled", False))
            else "match_video",
        }

    def run_hot_follow_compose(
        self,
        task_id: str,
        task: dict,
        request: HotFollowComposeRequestContract,
        *,
        repo: Any,
        policy_upsert: Callable[[Any, str, dict[str, Any]], Any],
        hub_loader: Callable[[str, Any], dict[str, Any]],
        subtitle_resolver: Callable[[dict, str, str], str | None],
        subtitle_only_check: Callable[[str, dict], bool],
        revision_snapshot: Callable[[dict], dict[str, str | None]] | None = None,
        lipsync_runner: Callable[[str, bool], str | None] | None = None,
        object_exists_fn: Callable[[str], bool] = object_exists,
        object_head_fn: Callable[[str], dict | None] = object_head,
        media_meta_from_head_fn: Callable[[dict | None], tuple[int, str | None]] = media_meta_from_head,
        compose_runner: Callable[[str, dict], dict[str, Any]] | None = None,
    ) -> HotFollowComposeResponseContract:
        """Run the full Hot Follow compose flow behind a service contract."""
        revision_snapshot = revision_snapshot or (lambda current_task: {})
        compose_runner = compose_runner or (
            lambda current_task_id, current_task: self.compose(
                current_task_id,
                current_task,
                subtitle_resolver=subtitle_resolver,
                subtitle_only_check=subtitle_only_check,
            )
        )
        lipsync_runner = lipsync_runner or (lambda _task_id, _enabled: None)

        compose_lock_until = task.get("compose_lock_until")
        if compose_lock_until:
            try:
                lock_dt = (
                    datetime.fromisoformat(str(compose_lock_until))
                    if isinstance(compose_lock_until, str)
                    else compose_lock_until
                )
                if lock_dt.tzinfo is None:
                    lock_dt = lock_dt.replace(tzinfo=timezone.utc)
                if lock_dt > datetime.now(timezone.utc):
                    current = repo.get(task_id) or task
                    policy_upsert(
                        repo,
                        task_id,
                        {
                            "compose_status": "running",
                            "compose_last_status": "running",
                            "compose_last_started_at": current.get("compose_last_started_at")
                            or datetime.now(timezone.utc).isoformat(),
                            "compose_last_finished_at": None,
                        },
                    )
                    return HotFollowComposeResponseContract(
                        status_code=409,
                        body={
                            "error": "compose_in_progress",
                            "status": "running",
                            "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
                            "task_id": task_id,
                        },
                    )
            except Exception:
                pass

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

        lock = task_compose_lock(task_id)
        if not lock.acquire(blocking=False):
            current = repo.get(task_id) or task
            policy_upsert(
                repo,
                task_id,
                {
                    "compose_status": "running",
                    "compose_last_status": "running",
                    "compose_last_started_at": current.get("compose_last_started_at")
                    or datetime.now(timezone.utc).isoformat(),
                    "compose_last_finished_at": None,
                },
            )
            return HotFollowComposeResponseContract(
                status_code=409,
                body={
                    "error": "compose_in_progress",
                    "status": "running",
                    "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
                    "task_id": task_id,
                },
            )

        try:
            current_for_plan = repo.get(task_id) or task
            current_for_plan = self._apply_request_mutations(repo, task_id, current_for_plan, request, policy_upsert)

            final_key = (
                task_key(current_for_plan, "final_video_key")
                or task_key(current_for_plan, "final_video_path")
                or deliver_key(task_id, "final.mp4")
            )
            final_meta = object_head_fn(str(final_key)) if final_key else None
            final_size, _ = media_meta_from_head_fn(final_meta)
            final_physically_exists = bool(
                final_key and object_exists_fn(str(final_key)) and final_size >= MIN_VIDEO_BYTES
            )
            if final_physically_exists and not request.force:
                revision_for_freshness = revision_snapshot(current_for_plan)
                if _current_final_is_fresh(
                    current_for_plan,
                    revision=revision_for_freshness,
                    final_exists=True,
                    final_size=final_size,
                ):
                    policy_upsert(repo, task_id, {"compose_lock_until": None})
                    return HotFollowComposeResponseContract(
                        status_code=200,
                        body={
                            "task_id": task_id,
                            "final_url": task_endpoint(task_id, "final"),
                            "final_video_url": task_endpoint(task_id, "final"),
                            "final_key": str(final_key),
                            "hub": hub_loader(task_id, repo),
                        },
                    )

            compose_plan = self._build_compose_plan(current_for_plan)
            policy_upsert(
                repo,
                task_id,
                {"compose_lock_until": (datetime.now(timezone.utc) + timedelta(seconds=300)).isoformat()},
            )
            policy_upsert(
                repo,
                task_id,
                {
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
                    "compose_plan": compose_plan,
                    "scene_outputs": current_for_plan.get("scene_outputs") or [],
                },
            )

            env_lipsync_enabled = str(os.getenv("HF_LIPSYNC_ENABLED", "0")).strip().lower() in ("1", "true", "yes")
            lipsync_warning = lipsync_runner(task_id, env_lipsync_enabled)
            if lipsync_warning:
                policy_upsert(repo, task_id, {"compose_warning": lipsync_warning})

            updates = compose_runner(task_id, repo.get(task_id) or current_for_plan)
            if lipsync_warning:
                current_warning = str(updates.get("compose_warning") or "").strip()
                updates["compose_warning"] = (
                    f"{current_warning} {lipsync_warning}".strip() if current_warning else lipsync_warning
                )
            policy_upsert(repo, task_id, updates)

            latest = repo.get(task_id) or current_for_plan
            resolved_key = task_key(latest, "final_video_key") or task_key(latest, "final_video_path")
            return HotFollowComposeResponseContract(
                status_code=200,
                body={
                    "task_id": task_id,
                    "final_url": task_endpoint(task_id, "final"),
                    "final_video_url": task_endpoint(task_id, "final"),
                    "final_key": str(resolved_key or ""),
                    "hub": hub_loader(task_id, repo),
                    "compose_status": latest.get("compose_status"),
                },
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"reason": "compose_failed", "message": str(exc.detail)}
            policy_upsert(
                repo,
                task_id,
                {
                    "compose_status": "failed",
                    "compose_error": detail,
                    "compose_error_reason": detail.get("reason"),
                    "compose_last_status": "failed",
                    "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
                    "compose_last_error": detail.get("message") or str(exc.detail),
                    "status": "failed",
                    "last_step": "compose",
                    "final_video_key": None,
                    "final_video_path": None,
                },
            )
            raise
        except Exception as exc:
            detail = {"reason": "compose_failed", "message": str(exc)}
            policy_upsert(
                repo,
                task_id,
                {
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
                },
            )
            raise HTTPException(status_code=409, detail=detail) from exc
        finally:
            try:
                policy_upsert(repo, task_id, {"compose_lock_until": None})
            finally:
                lock.release()

    # ── Phase 1: Validation ───────────────────────────────────────────────

    def _validate_inputs(
        self,
        task_id: str,
        task: dict,
        subtitle_only_check: Callable[[str, dict], bool],
    ) -> _ComposeInputs:
        voice_state = collect_voice_execution_state(task, self._settings)
        subtitle_only_compose = subtitle_only_check(task_id, task)

        # Resolve artifact keys
        from gateway.app.services.task_view_helpers import task_key as _task_key  # noqa: PLC0415

        video_key = (
            _task_key(task, "mute_video_key")
            or _task_key(task, "mute_video_path")
            or _task_key(task, "raw_path")
        )
        audio_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")

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
        config = dict(task.get("config") or {})
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

        compose_plan = dict(task.get("compose_plan") or {})
        overlay_subtitles = bool(compose_plan.get("overlay_subtitles"))
        strip_subtitle_streams = bool(compose_plan.get("strip_subtitle_streams", True))
        cleanup_mode = str(compose_plan.get("cleanup_mode") or "none").strip().lower()
        target_lang = str(
            compose_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang") or "mm"
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
        voice_duration = 0.0
        if inputs.audio_key and not inputs.subtitle_only_compose:
            try:
                _, voice_duration = assert_local_audio_ok(voice_path)
            except ValueError:
                compose_fail("missing_voiceover", "voiceover audio invalid")

        video_input_path = video_path
        compose_policy = inputs.compose_policy
        compose_warning: str | None = None

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

        if overlay_subtitles:
            if not bundled_myanmar_ttf.exists() or bundled_myanmar_ttf.stat().st_size == 0:
                compose_fail("font_missing", f"bundled Myanmar font missing: {bundled_myanmar_ttf}")
            subtitle_key = subtitle_resolver(task, task_id, inputs.target_lang)
            if not subtitle_key:
                compose_fail("subtitles_missing", "overlay_subtitles enabled but target subtitle key is missing")
            self._storage.download_file(str(subtitle_key), str(subtitle_path))
            if not subtitle_path.exists() or subtitle_path.stat().st_size == 0:
                if inputs.subtitle_only_compose:
                    # Historical fix (267744a): no-speech task with empty subtitle —
                    # skip overlay, compose succeeds without burned-in text.
                    overlay_subtitles = False
                else:
                    compose_fail("subtitles_missing", "overlay_subtitles enabled but subtitle file is empty")

        # ── BGM download ──
        bgm_path: Path | None = None
        if inputs.bgm_key:
            bgm_path = tmp / "bgm_input.mp3"
            self._storage.download_file(str(inputs.bgm_key), str(bgm_path))

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
            compose_warning=compose_warning,
            overlay_subtitles=overlay_subtitles,
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
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            stderr_tail = str(exc.stderr or "")[-800:]
            compose_fail(
                "compose_timeout",
                f"{purpose} timed out after {effective_timeout}s",
                ffmpeg_cmd=" ".join(cmd),
                stderr_tail=stderr_tail,
            )
        return proc  # type: ignore[possibly-undefined]

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
        if ws.bgm_path and ws.bgm_path.exists():
            self._compose_subtitle_only_with_bgm(ws, inputs)
        else:
            self._compose_subtitle_only_no_bgm(ws, inputs)

    def _compose_subtitle_only_with_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode)
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
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode)
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
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode)
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

    def _compose_voice_only(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice without BGM.  Includes CRF23 fallback retry."""
        voice_filter = self._voice_filter_expr(ws)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode)
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
        final_size: int,
        final_duration: float,
        compose_started_at: str,
        compose_policy: str,
        freeze_tail_cap_sec: float,
        compose_warning: str | None,
        ffmpeg_cmd_used: str | None,
    ) -> dict[str, Any]:
        """Upload final video, verify, and build the 27-field return dict."""
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
        return {
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
            "final_source_subtitles_content_hash": str(task.get("subtitles_content_hash") or "").strip() or None,
            "final_source_subtitle_updated_at": str(task.get("subtitles_override_updated_at") or "").strip() or None,
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
            "last_step": "compose",
            "status": "ready",
            "error_message": None,
            "error_reason": None,
        }

"""Matrix Script Tomato Real Result — controlled orchestrator (PR-A).

The single controlled path for the fixed case 《海边与圣女果的盛夏约定》:

    fixed tomato plan → asset→shot mapping → real-asset image→motion shots
      → burned operator-language captions
      → Azure TTS (only if env present) else honest silent fallback
      → ffmpeg assembly (reused) → final.mp4
      → artifact staging (reused) → preview-able staged candidate (reused)
      → operator acceptance gate (L3)

Reuses the existing substrate verbatim: ``assemble_final_video`` /
``generate_silent_audio`` / ``probe_duration_seconds`` (simple_scene_renderer),
``stage_minimal_result`` (artifact staging), ``staged_record_to_delivery_block``
(delivery view). It does NOT modify any of them and does NOT touch
``artifact_storage.py``.

Hard boundary: ``official_publish_ready=false``; no provider name / URL / Akool
id / model / credit / publish field in the payload; a fallback-only result
fails operator acceptance and is never a delivery candidate; ffmpeg absence
raises (never a fake final.mp4).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    stage_minimal_result,
)
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    GENERATION_PROVIDER_NONE,
    assert_no_delivery_view_forbidden_tokens,
    staged_record_to_delivery_block,
)
from gateway.app.services.matrix_script.real_asset_scene_renderer import (
    overlay_caption,
    render_caption_png,
)
from gateway.app.services.matrix_script import ffmpeg_backbone as backbone
from gateway.app.services.matrix_script import voiceover_capability
from gateway.app.services.matrix_script import akool_image_to_video_capability as akool_i2v
from gateway.app.services.matrix_script import generation_plan_view as gen_plan
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    assemble_final_video,
    ffmpeg_available,
    ffmpeg_path,
    generate_silent_audio,
    probe_duration_seconds,
)
from gateway.app.services.matrix_script.tomato_acceptance_gate import (
    ShotRenderFact,
    compute_tomato_acceptance,
    fallback_only_acceptance,
)
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

LINE_ID = "matrix_script"
# Operator-visible scene clips are rendered through the proven ffmpeg backbone
# (Owner-approved S5→S8 backbone integration): deterministic 1080×1920 / 30fps
# Ken-Burns proxy from each shot's still, with the existing Pillow caption overlay
# preserved on top, then ffprobe QC on the composed final.mp4. The backbone is a
# fast-preview proxy — NOT generative, NOT publish-ready.
DEFAULT_WIDTH = backbone.BACKBONE_WIDTH      # 1080
DEFAULT_HEIGHT = backbone.BACKBONE_HEIGHT     # 1920
DEFAULT_FPS = backbone.BACKBONE_FPS           # 30
DEFAULT_SHOT_SECONDS = 4.0
AUDIO_MODE_AZURE = "azure_tts"
AUDIO_MODE_EDGE = "edge_tts"
AUDIO_MODE_SILENT = "silent_fallback"
CAPTION_MODE_BURNED = "burned_in"
CAPTION_MODE_SIDECAR = "sidecar_only"

# Scene engine + per-shot render-mode markers recorded on the manifest (operator-safe).
SCENE_ENGINE_BACKBONE = "ffmpeg_backbone"
RENDER_MODE_PROXY = "ffmpeg_backbone_proxy"
RENDER_MODE_STATIC = "ffmpeg_backbone_static_still"
# Vendor-agnostic render-mode token (the capability KIND, never the vendor name).
RENDER_MODE_AKOOL = "provider_image_to_video"

# The single shot that attempts real Akool image_to_video generation when enabled
# (a real-visual product shot). One shot per run keeps provider cost bounded.
AKOOL_SHOT_ID = "shot02"

_DEFAULT_VOICE = voiceover_capability.DEFAULT_VOICE


class TomatoRealResultError(ValueError):
    """Raised on an invalid tomato real-result input."""


@dataclass(frozen=True)
class TomatoRealResult:
    task_id: Optional[str]
    case_id: str
    script_title: str
    audio_mode: str
    caption_mode: str
    final_video_path: str
    duration_seconds: float
    width: int
    height: int
    delivery_block: Mapping[str, Any]
    acceptance: Mapping[str, Any]
    shot_checklist: Tuple[Mapping[str, Any], ...]
    # P1-3 PR-D — shots whose UPLOADED material bytes the renderer actually
    # consumed (image used directly / video first frame extracted). Empty unless
    # a resolvable ``msmaterial://`` override was supplied AND used.
    consumed_material_shot_ids: Tuple[str, ...] = ()
    # Operator-visible ffmpeg-backbone integration (Owner-approved S5→S8):
    # scene_engine + operator-safe ffprobe QC scalars from the composed final.mp4.
    scene_engine: str = SCENE_ENGINE_BACKBONE
    qc_passed: Optional[bool] = None
    qc_resolution: Optional[str] = None
    # Real-video heavy batch: voiceover status + operator-safe capability status.
    voiceover_status: str = voiceover_capability.STATUS_BLOCKED_CREDENTIAL_MISSING
    capability_status: Mapping[str, Any] = field(default_factory=dict)
    official_publish_ready: bool = False
    line_id: str = LINE_ID


def _task_id(task: Mapping[str, Any]) -> Optional[str]:
    for key in ("task_id", "id"):
        v = task.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def _pad_audio_to(in_path: str, out_wav: str, duration_seconds: float) -> None:
    cmd = [
        ffmpeg_path(), "-y", "-i", in_path,
        "-af", "apad", "-t", f"{float(duration_seconds):.3f}",
        "-ar", "44100", "-ac", "1", out_wav,
    ]
    import subprocess

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    if proc.returncode != 0:
        raise TomatoRealResultError("audio pad/convert failed")


def _build_manifest(
    *, task_id: Optional[str], shot_facts: List[ShotRenderFact],
    audio_mode: str, caption_mode: str, duration_seconds: float,
    width: int, height: int,
    final_rel: str, audio_rel: str, subtitle_rel: str, scene_rels: List[str],
    scene_engine: str = SCENE_ENGINE_BACKBONE,
    per_shot_render: Optional[List[Dict[str, Any]]] = None,
    capability_status: Optional[Mapping[str, Any]] = None,
    voiceover_status: Optional[str] = None,
    qc: Optional[Mapping[str, Any]] = None,
    backbone_summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "manifest_version": "matrix_script_tomato_real_result_v1",
        "line_id": LINE_ID,
        "case_id": plan_mod.CASE_ID,
        "script_title": plan_mod.SCRIPT_TITLE,
        "task_id": task_id,
        # L1 pipeline step status (all derived from real execution).
        "pipeline_steps": {
            "asset_ingestion": "done",
            "shot_assembly": "done",
            "audio_generation": audio_mode,
            "subtitle_generation": "done",
            "final_assembly": "done",
            "artifact_staging": "done",
        },
        "audio_mode": audio_mode,
        "voiceover_status": voiceover_status,
        "caption_mode": caption_mode,
        "scene_engine": scene_engine,
        "shot_count": len(shot_facts),
        "duration_seconds": float(duration_seconds),
        "resolution": f"{width}x{height}",
        "shots": [
            {"shot_id": f.shot_id, "source": f.source,
             "real_visual": f.real_visual, "semantic_match": f.semantic_match}
            for f in shot_facts
        ],
        "final_video_path": final_rel,
        "audio_path": audio_rel,
        "subtitle_path": subtitle_rel,
        "scene_clip_paths": list(scene_rels),
    }
    # Additive backbone evidence (operator-safe; no local_path / provider field).
    if per_shot_render is not None:
        manifest["per_shot_render"] = [dict(r) for r in per_shot_render]
    if capability_status is not None:
        manifest["capability_status"] = dict(capability_status)
    if qc is not None:
        manifest["qc"] = dict(qc)
    if backbone_summary is not None:
        manifest["backbone"] = dict(backbone_summary)
    return manifest


def _fmt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    s = (total_ms // 1000) % 60
    m = (total_ms // 60000) % 60
    h = total_ms // 3600000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _extract_first_video_frame(video_path: str, work_dir: str, shot_id: str) -> Optional[str]:
    """Extract the first frame of an uploaded video as a still PNG for rendering.

    Returns the frame path when ffmpeg successfully decodes a frame, else None
    (the caller then keeps the shot's default asset and does NOT mark the
    material as consumed — honest: the uploaded bytes were not used).
    """
    out_png = os.path.join(work_dir, f"{shot_id}_material_frame.png")
    cmd = [
        ffmpeg_path(), "-y", "-i", video_path,
        "-frames:v", "1", "-q:v", "2", out_png,
    ]
    import subprocess

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    if proc.returncode == 0 and os.path.exists(out_png) and os.path.getsize(out_png) > 0:
        return out_png
    return None


def _resolve_shot_render_source(
    shot_id: str,
    default_image: str,
    material_overrides: Optional[Mapping[str, Mapping[str, Any]]],
    work_dir: str,
) -> Tuple[str, bool]:
    """Pick the visual source for a shot; return ``(path, consumed_uploaded_bytes)``.

    When an uploaded material override resolves to readable local bytes the
    renderer uses them: an image is used directly; a video has its first frame
    extracted. Anything that does not resolve (missing bytes, unsupported kind,
    failed frame extraction) falls back to the shot's default asset and is
    reported as NOT consumed — the V2 candidate must never claim it used bytes it
    did not.
    """
    if not material_overrides:
        return default_image, False
    override = material_overrides.get(shot_id)
    if not isinstance(override, Mapping):
        return default_image, False
    src = override.get("local_path")
    if not isinstance(src, str) or not src or not os.path.exists(src) or os.path.getsize(src) <= 0:
        return default_image, False
    kind = str(override.get("material_kind") or "")
    if kind == "image":
        return src, True
    if kind == "video":
        frame = _extract_first_video_frame(src, work_dir, shot_id)
        if frame:
            return frame, True
        return default_image, False
    return default_image, False


@dataclass(frozen=True)
class _BackboneShotRender:
    """Per-shot backbone render outcome (internal)."""

    render_mode: str          # RENDER_MODE_PROXY | RENDER_MODE_STATIC
    caption_burned: bool


def _render_shot_via_backbone(
    still_path: str,
    work_dir: str,
    out_clip: str,
    *,
    shot,
    duration_seconds: float,
) -> _BackboneShotRender:
    """Render one operator-visible shot clip through the ffmpeg backbone.

    1. Ken-Burns **proxy** (deterministic 1080×1920 / 30fps) from the resolved
       still via :func:`backbone.generate_with_fallback` — on render failure the
       backbone itself falls back to a static-still clip (no fake clip is produced).
    2. The existing Pillow caption PNG is overlaid on top (this build has no
       drawtext/libass), preserving burned-in captions where a CJK font exists;
       when no font is available the motion clip is promoted as-is and the run
       still emits the .srt sidecar (honest, unchanged behavior).

    The backbone is a fast-preview proxy: non-generative, ``official_publish_ready``
    stays false. Returns the per-shot render mode + whether a caption was burned.
    """
    zoom = backbone.ZOOM_IN if shot.order % 2 else backbone.ZOOM_OUT
    motion_path = os.path.join(work_dir, f"{shot.shot_id}_backbone.mp4")
    clip = backbone.generate_with_fallback(
        still_path, motion_path, duration_seconds=float(duration_seconds), zoom=zoom
    )
    render_mode = (
        RENDER_MODE_STATIC if clip.tier == backbone.TIER_STATIC_STILL else RENDER_MODE_PROXY
    )
    caption_burned = _overlay_caption_or_promote(motion_path, out_clip, shot=shot, work_dir=work_dir)
    return _BackboneShotRender(render_mode=render_mode, caption_burned=caption_burned)


def _overlay_caption_or_promote(motion_path: str, out_clip: str, *, shot, work_dir: str) -> bool:
    """Burn the shot caption onto a motion clip (1080×1920) or promote it as-is.

    Shared by the backbone and the Akool image_to_video paths so both carry the same
    burned-in caption behavior. Returns whether a caption was burned.
    """
    caption_text = (shot.subtitle_zh or "").strip()
    if caption_text:
        caption_png = render_caption_png(
            caption_text,
            os.path.join(work_dir, f"{shot.shot_id}_caption.png"),
            width=backbone.BACKBONE_WIDTH,
            height=backbone.BACKBONE_HEIGHT,
        )
        if caption_png:
            overlay_caption(motion_path, caption_png, out_clip)
            return True
    os.replace(motion_path, out_clip)
    return False


def _narration_text(shots) -> str:
    """Operator-script narration text for the whole timeline (shot voiceover lines)."""
    parts = [str(getattr(s, "voiceover_zh", "") or "").strip() for s in shots]
    return "  ".join(p for p in parts if p)


# Indirection so tests can monkeypatch the voiceover synth without network/secret.
def _voiceover_synth(text, out_path, *, env, voice):
    return voiceover_capability.synthesize_narration(
        text, out_path, env=env, voice=voice
    )


def _build_capability_status(
    *, voiceover, any_caption_burned: bool, env: Optional[Mapping[str, str]],
    akool_result: Optional["akool_i2v.AkoolShotResult"] = None,
    provider_target_shot_id: Optional[str] = None,
    provider_prompt_meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Operator-safe capability status for voiceover / image_to_video / subtitles / bgm.

    Honest by construction: no provider/vendor brand in the operator label; no secret
    (only credential presence is checked); a missing capability is reported as blocked /
    not-selected, never faked. When a real Akool image_to_video one-shot was attempted,
    its honest per-shot status is surfaced directly.
    """
    src = env if env is not None else os.environ
    if akool_result is not None:
        image_to_video = akool_result.to_status_dict()
    else:
        akool_ready = akool_i2v.real_enabled(src) and akool_i2v.credentials_present(src)
        image_to_video = {
            "capability": "image_to_video",
            "status": ("available_not_run" if akool_ready else akool_i2v.STATUS_CREDENTIAL_MISSING),
            "provider_attempted": False,
            "succeeded": False,
            "operator_label_zh": (
                "AI 视频生成可用（未启用）" if akool_ready
                else "AI 视频生成未启用 · 缺少凭证（使用镜头代理）"
            ),
        }
    # PR-4: operator-safe provider-target evidence for the V1/V2 change explanation —
    # which shot the provider targeted, the resolved material role, an operator-safe
    # generation summary, and a script-directed flag. NEVER the raw provider prompt /
    # URL / vendor (only surfaced when a script-directed provider attempt was made).
    if provider_prompt_meta is not None:
        image_to_video = dict(image_to_video)
        image_to_video["provider_target_shot_id"] = provider_target_shot_id
        image_to_video["material_role"] = provider_prompt_meta.get("material_role")
        image_to_video["material_role_label_zh"] = provider_prompt_meta.get("material_role_label_zh")
        image_to_video["generation_summary_zh"] = provider_prompt_meta.get("diagnostic_summary_zh")
        image_to_video["script_directed"] = True
    return {
        "scene_engine": SCENE_ENGINE_BACKBONE,
        "image_to_video": image_to_video,
        "voiceover": voiceover.to_status_dict(),
        "subtitles": {
            "capability": "subtitles",
            "status": "generated" if any_caption_burned else "sidecar_only",
            "operator_label_zh": "字幕已烧录" if any_caption_burned else "字幕（外挂文件）",
        },
        "bgm": {
            "capability": "bgm",
            "status": "not_selected",
            "operator_label_zh": "配乐未选择",
        },
    }


def _write_srt(path: str, shots, durations: List[float]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines: List[str] = []
    cursor = 0.0
    for i, (shot, dur) in enumerate(zip(shots, durations), start=1):
        start, end = cursor, cursor + float(dur)
        cursor = end
        lines += [str(i), f"{_fmt_ts(start)} --> {_fmt_ts(end)}", shot.subtitle_zh, ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).strip() + "\n")


def run_tomato_real_result(
    task: Mapping[str, Any],
    output_dir: "str | os.PathLike[str]",
    *,
    sink: Any,
    asset_dir: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    voice: str = _DEFAULT_VOICE,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    fps: int = DEFAULT_FPS,
    material_overrides: Optional[Mapping[str, Mapping[str, Any]]] = None,
    active_shot_id: Optional[str] = None,
) -> TomatoRealResult:
    """Run the controlled tomato real-result path; return a staged, gated result.

    ``material_overrides`` (P1-3 PR-D) maps a shot_id → ``{local_path,
    material_kind}`` for an operator-UPLOADED material whose bytes are resolvable.
    When supplied, the matching shot is rendered from those bytes instead of its
    default asset (image used directly; video first frame extracted) and the shot
    is reported in ``consumed_material_shot_ids``. An override that does not
    resolve leaves the shot on its default asset and is NOT reported consumed.
    """
    if not isinstance(task, Mapping):
        raise TomatoRealResultError("task must be a mapping")
    if sink is None or not hasattr(sink, "put"):
        raise TomatoRealResultError("sink must provide a put(local_path, artifact_name) method")
    if not ffmpeg_available():
        raise FFmpegUnavailableError(
            "ffmpeg/ffprobe not found on PATH; the tomato real-result path cannot "
            "produce a real final.mp4 in this environment."
        )

    task_id = _task_id(task)
    output_dir = os.fspath(output_dir)
    asset_dir = asset_dir or plan_mod.default_asset_dir()
    shots = list(plan_mod.TOMATO_SHOTS)
    # PR-4: the Current Shot Panel active shot is the provider-target; default to the
    # designated product shot (shot02) when none / an unknown id is supplied (safe
    # default behavior — bounded to ONE controlled shot per run).
    _shot_ids = {s.shot_id for s in shots}
    provider_target_id = active_shot_id if active_shot_id in _shot_ids else AKOOL_SHOT_ID

    shots_dir = os.path.join(output_dir, "shots")
    audio_dir = os.path.join(output_dir, "audio")
    subs_dir = os.path.join(output_dir, "subtitles")
    final_dir = os.path.join(output_dir, "final")
    work_dir = os.path.join(output_dir, ".work")
    for d in (shots_dir, audio_dir, subs_dir, final_dir, work_dir):
        os.makedirs(d, exist_ok=True)

    # 1. Fixed per-shot durations (deterministic timeline; voiceover is composed as
    #    one real TTS narration track over the whole timeline in step 3).
    durations: List[float] = [DEFAULT_SHOT_SECONDS for _ in shots]

    # Real Akool image_to_video is attempted for ONE designated shot when enabled
    # (flag + credential). Any failure degrades to the backbone proxy with an honest
    # per-shot status — never a fake provider clip.
    akool_enabled = akool_i2v.real_enabled(env) and akool_i2v.credentials_present(env)
    akool_shot_result: Optional[akool_i2v.AkoolShotResult] = None
    provider_prompt_meta: Optional[Dict[str, Any]] = None

    # 2. Render each shot clip. The designated shot attempts real Akool image_to_video
    #    (when enabled); every other shot renders THROUGH THE FFMPEG BACKBONE (image →
    #    1080×1920 Ken-Burns proxy). The SOURCE pixels may be swapped for resolvable
    #    uploaded/replacement material bytes (#212). Captions burned on all paths.
    scene_clip_paths: List[str] = []
    shot_facts: List[ShotRenderFact] = []
    checklist: List[Dict[str, Any]] = []
    consumed_material_shot_ids: List[str] = []
    per_shot_render: List[Dict[str, Any]] = []
    any_caption_burned = False
    for shot, dur in zip(shots, durations):
        image_path = os.path.join(asset_dir, shot.asset_filename)
        out_clip = os.path.join(shots_dir, f"{shot.shot_id}.mp4")
        rendered = False
        # Default-asset existence gates whether this shot renders (keeps the
        # rendered-shot set 1:1 with the downstream audio/subtitle alignment);
        # the SOURCE pixels may be swapped for resolvable uploaded material bytes.
        if os.path.exists(image_path):
            render_source, consumed = _resolve_shot_render_source(
                shot.shot_id, image_path, material_overrides, work_dir
            )
            ak: Optional[akool_i2v.AkoolShotResult] = None
            if akool_enabled and shot.shot_id == provider_target_id:
                # PR-4: build a SCRIPT-DIRECTED, role-driven provider prompt for the
                # active/provider-target shot (replaces the hardcoded DEFAULT_PROMPT).
                # Same role + motion resolution the Current Shot Panel shows. The
                # provider prompt is runtime-transient (passed here, never surfaced).
                provider_prompt_meta = gen_plan.build_provider_prompt_for_shot(shot, task)
                ak = akool_i2v.generate_shot_clip_akool(
                    still_path=render_source,
                    out_clip=os.path.join(work_dir, f"{shot.shot_id}_akool.mp4"),
                    task_id=task_id or LINE_ID, shot_id=shot.shot_id,
                    prompt=provider_prompt_meta["provider_prompt"], env=env,
                )
                akool_shot_result = ak
            if ak is not None and ak.succeeded:
                # Real provider clip → burn the caption on top (same as backbone path).
                cb = _overlay_caption_or_promote(ak.clip_path, out_clip, shot=shot, work_dir=work_dir)
                render_mode = RENDER_MODE_AKOOL
                any_caption_burned = any_caption_burned or cb
            else:
                # No Akool attempt, or it failed → honest backbone proxy fallback.
                render_out = _render_shot_via_backbone(
                    render_source, work_dir, out_clip, shot=shot, duration_seconds=dur,
                )
                render_mode = render_out.render_mode
                any_caption_burned = any_caption_burned or render_out.caption_burned
            rendered = True
            scene_clip_paths.append(out_clip)
            per_shot_render.append({"shot_id": shot.shot_id, "render_mode": render_mode})
            if consumed:
                consumed_material_shot_ids.append(shot.shot_id)
        shot_facts.append(ShotRenderFact(
            shot_id=shot.shot_id, source=shot.source, rendered=rendered,
            real_visual=shot.real_visual and rendered,
            semantic_match=shot.semantic_match and rendered,
        ))
        checklist.append({
            "shot_id": shot.shot_id,
            "title_zh": shot.title_zh,
            "expected_zh": shot.visual_intent_zh,
            "asset": shot.asset_filename,
            "source": shot.source,
            "rendered": rendered,
            "real_visual": shot.real_visual and rendered,
            "semantic_match": shot.semantic_match and rendered,
        })

    if not scene_clip_paths:
        # No real assets rendered at all → honest fallback-only verdict; no
        # fake final video, no delivery candidate.
        raise TomatoRealResultError(
            "no real assets rendered; fallback-only result is not an operator "
            "candidate (place the MS-TOMATO-BEACH-001 asset pack first)"
        )

    # Recompute durations to the actually-rendered shots (1:1 with scene clips).
    rendered_durations = [d for shot, d in zip(shots, durations)
                          if os.path.exists(os.path.join(asset_dir, shot.asset_filename))]

    # 3. Voiceover track for the whole timeline — REAL TTS narration where a path
    #    is available (credentialed Azure → keyless edge_tts), else honest silent
    #    fallback. Never fabricates audio; the status carries the honest block reason.
    rendered_shots_for_audio = [
        shot for shot in shots
        if os.path.exists(os.path.join(asset_dir, shot.asset_filename))
    ]
    total_timeline_seconds = float(sum(rendered_durations))
    audio_path = os.path.join(audio_dir, "narration.wav")
    narration_text = _narration_text(rendered_shots_for_audio)
    voiceover = _voiceover_synth(
        narration_text,
        os.path.join(audio_dir, "narration_tts.mp3"),
        env=env,
        voice=voice,
    )
    if voiceover.generated and voiceover.audio_path:
        # Compose the real narration into the timeline (pad/trim to total duration).
        try:
            _pad_audio_to(voiceover.audio_path, audio_path, total_timeline_seconds)
            audio_mode = (
                AUDIO_MODE_AZURE
                if voiceover.provider == voiceover_capability.PROVIDER_AZURE
                else AUDIO_MODE_EDGE
            )
        except Exception:  # noqa: BLE001 — compose failure degrades to honest silence
            generate_silent_audio(audio_path, duration_seconds=total_timeline_seconds)
            audio_mode = AUDIO_MODE_SILENT
            voiceover = voiceover_capability.VoiceoverOutcome(
                voiceover_capability.STATUS_BLOCKED_PROVIDER_FAIL,
                voiceover_capability.PROVIDER_NONE,
                None,
                "voiceover compose failed",
            )
    else:
        generate_silent_audio(audio_path, duration_seconds=total_timeline_seconds)
        audio_mode = AUDIO_MODE_SILENT

    # 4. Subtitles sidecar (.srt) for the rendered shots.
    rendered_shots = [shot for shot in shots
                      if os.path.exists(os.path.join(asset_dir, shot.asset_filename))]
    subtitle_path = os.path.join(subs_dir, "subtitles.srt")
    _write_srt(subtitle_path, rendered_shots, rendered_durations)

    # 5. Assemble final.mp4 (reused substrate).
    final_video_path = os.path.join(final_dir, "final.mp4")
    assemble_final_video(
        final_video_path, scene_clip_paths=scene_clip_paths,
        audio_path=audio_path, work_dir=work_dir,
    )
    duration_seconds = probe_duration_seconds(final_video_path)

    caption_mode = CAPTION_MODE_BURNED if any_caption_burned else CAPTION_MODE_SIDECAR

    # 5b. ffprobe QC on the composed operator-visible final.mp4 (backbone verdict).
    #     QC is evidence, never a publish gate; a probe failure must not kill an
    #     otherwise-playable result, so we degrade to qc=None honestly.
    qc: Optional[Dict[str, Any]] = None
    try:
        qc = backbone.qc_probe(
            final_video_path, expected_duration_seconds=float(sum(rendered_durations))
        )
    except Exception:  # noqa: BLE001 — QC is best-effort evidence, never a gate
        qc = None
    backbone_summary: Dict[str, Any] = {
        "engaged": True,
        "scene_engine": SCENE_ENGINE_BACKBONE,
        "tier": backbone.TIER_PROXY,
        "is_generative": False,
        "official_publish_ready": False,
        "qc_passed": (bool(qc.get("passed")) if isinstance(qc, Mapping) else None),
        "note": "镜头代理（1080×1920）+ 字幕叠加 + 拼接 + ffprobe 质检；非生成式、非最终成片。",
    }

    # 5c. Operator-safe capability status (voiceover / image_to_video / subtitles / bgm).
    capability_status = _build_capability_status(
        voiceover=voiceover, any_caption_burned=any_caption_burned, env=env,
        akool_result=akool_shot_result,
        provider_target_shot_id=provider_target_id,
        provider_prompt_meta=provider_prompt_meta,
    )

    # 6. Manifest (real local relative paths only).
    manifest = _build_manifest(
        task_id=task_id, shot_facts=shot_facts, audio_mode=audio_mode,
        caption_mode=caption_mode, duration_seconds=duration_seconds,
        width=width, height=height,
        final_rel=os.path.relpath(final_video_path, output_dir),
        audio_rel=os.path.relpath(audio_path, output_dir),
        subtitle_rel=os.path.relpath(subtitle_path, output_dir),
        scene_rels=[os.path.relpath(p, output_dir) for p in scene_clip_paths],
        scene_engine=SCENE_ENGINE_BACKBONE,
        per_shot_render=per_shot_render,
        capability_status=capability_status,
        voiceover_status=voiceover.status,
        qc=qc,
        backbone_summary=backbone_summary,
    )
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    # 7. Stage the pack (reused) → artifact_staged refs + preview url.
    record = stage_minimal_result(
        sink=sink, task_id=task_id,
        final_video_path=final_video_path, manifest_path=manifest_path,
        subtitles_path=subtitle_path, audio_path=audio_path,
        scene_clip_paths=tuple(scene_clip_paths),
    )

    # 8. Delivery staged-candidate block (reused; provider label stays "none").
    delivery_block = staged_record_to_delivery_block(record, generation_provider=GENERATION_PROVIDER_NONE)

    # 9. Operator acceptance gate (L3).
    acceptance = compute_tomato_acceptance(shot_facts)

    return TomatoRealResult(
        task_id=task_id,
        case_id=plan_mod.CASE_ID,
        script_title=plan_mod.SCRIPT_TITLE,
        audio_mode=audio_mode,
        caption_mode=caption_mode,
        final_video_path=final_video_path,
        duration_seconds=float(duration_seconds),
        width=width,
        height=height,
        delivery_block=delivery_block,
        acceptance=acceptance.to_dict(),
        shot_checklist=tuple(checklist),
        consumed_material_shot_ids=tuple(consumed_material_shot_ids),
        scene_engine=SCENE_ENGINE_BACKBONE,
        qc_passed=(bool(qc.get("passed")) if isinstance(qc, Mapping) else None),
        qc_resolution=(str(qc.get("resolution")) if isinstance(qc, Mapping) and qc.get("resolution") else None),
        voiceover_status=voiceover.status,
        capability_status=capability_status,
    )


def tomato_result_to_payload(result: TomatoRealResult) -> Dict[str, object]:
    """Operator-safe JSON payload: staged delivery block + L3 acceptance + meta."""
    payload: Dict[str, object] = dict(result.delivery_block)
    payload.update(result.acceptance)
    payload["task_id"] = result.task_id
    payload["case_id"] = result.case_id
    payload["script_title"] = result.script_title
    payload["audio_mode"] = result.audio_mode
    payload["caption_mode"] = result.caption_mode
    payload["duration_seconds"] = result.duration_seconds
    payload["resolution"] = f"{result.width}x{result.height}"
    payload["official_publish_ready"] = False
    payload["shot_checklist"] = [dict(s) for s in result.shot_checklist]
    # Operator-safe ffmpeg-backbone evidence (additive; no provider/publish token).
    payload["scene_engine"] = result.scene_engine
    payload["backbone_qc_passed"] = result.qc_passed
    payload["backbone_qc_resolution"] = result.qc_resolution
    # Real-video heavy batch: voiceover + capability status (operator-safe labels only).
    payload["voiceover_status"] = result.voiceover_status
    payload["capability_status"] = dict(result.capability_status or {})
    assert_no_delivery_view_forbidden_tokens(payload)
    return payload

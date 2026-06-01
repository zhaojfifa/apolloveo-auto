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

import asyncio
import json
import os
from dataclasses import dataclass
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
    render_shot_clip,
)
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
DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 1280
DEFAULT_FPS = 25
DEFAULT_SHOT_SECONDS = 4.0
AUDIO_MODE_AZURE = "azure_tts"
AUDIO_MODE_SILENT = "silent_fallback"
CAPTION_MODE_BURNED = "burned_in"
CAPTION_MODE_SIDECAR = "sidecar_only"

_AZURE_KEY_ENV = "AZURE_SPEECH_KEY"
_AZURE_REGION_ENV = "AZURE_SPEECH_REGION"
_DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


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
    official_publish_ready: bool = False
    line_id: str = LINE_ID


def _task_id(task: Mapping[str, Any]) -> Optional[str]:
    for key in ("task_id", "id"):
        v = task.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def _azure_env(env: Optional[Mapping[str, str]]) -> Optional[Tuple[str, str]]:
    src = env if env is not None else os.environ
    key = (src.get(_AZURE_KEY_ENV) or "").strip()
    region = (src.get(_AZURE_REGION_ENV) or "").strip()
    if key and region:
        return key, region
    return None


def _synthesize_shot_audio_azure(text: str, out_mp3: str, *, voice: str, key: str, region: str) -> None:
    from gateway.app.providers.azure_speech import generate_audio_azure_speech

    asyncio.run(
        generate_audio_azure_speech(
            text, voice, out_mp3, speech_key=key, speech_region=region,
        )
    )


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


def _concat_wavs(wav_paths: List[str], out_wav: str, work_dir: str) -> None:
    list_path = os.path.join(work_dir, "audio_concat.txt")
    with open(list_path, "w", encoding="utf-8") as fh:
        for p in wav_paths:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [
        ffmpeg_path(), "-y", "-f", "concat", "-safe", "0", "-i", list_path,
        "-ar", "44100", "-ac", "1", out_wav,
    ]
    import subprocess

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    if proc.returncode != 0:
        raise TomatoRealResultError("audio concat failed")


def _build_manifest(
    *, task_id: Optional[str], shot_facts: List[ShotRenderFact],
    audio_mode: str, caption_mode: str, duration_seconds: float,
    width: int, height: int,
    final_rel: str, audio_rel: str, subtitle_rel: str, scene_rels: List[str],
) -> Dict[str, Any]:
    return {
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
        "caption_mode": caption_mode,
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


def _fmt_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    s = (total_ms // 1000) % 60
    m = (total_ms // 60000) % 60
    h = total_ms // 3600000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


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
) -> TomatoRealResult:
    """Run the controlled tomato real-result path; return a staged, gated result."""
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

    shots_dir = os.path.join(output_dir, "shots")
    audio_dir = os.path.join(output_dir, "audio")
    subs_dir = os.path.join(output_dir, "subtitles")
    final_dir = os.path.join(output_dir, "final")
    work_dir = os.path.join(output_dir, ".work")
    for d in (shots_dir, audio_dir, subs_dir, final_dir, work_dir):
        os.makedirs(d, exist_ok=True)

    azure = _azure_env(env)
    audio_mode = AUDIO_MODE_AZURE if azure else AUDIO_MODE_SILENT

    # 1. Per-shot audio (Azure if env) → decides per-shot duration; else fixed.
    durations: List[float] = []
    shot_audio_paths: List[Optional[str]] = []
    for shot in shots:
        if azure:
            key, region = azure
            mp3 = os.path.join(audio_dir, f"{shot.shot_id}.mp3")
            try:
                _synthesize_shot_audio_azure(shot.voiceover_zh, mp3, voice=voice, key=key, region=region)
                dur = max(min(probe_duration_seconds(mp3) + 0.5, 9.0), 3.0)
            except Exception:
                # Azure failed mid-run → degrade this shot to silent timing.
                mp3 = None
                dur = DEFAULT_SHOT_SECONDS
            shot_audio_paths.append(mp3)
            durations.append(dur)
        else:
            shot_audio_paths.append(None)
            durations.append(DEFAULT_SHOT_SECONDS)

    # 2. Render each shot clip from its real asset (image → motion + caption).
    scene_clip_paths: List[str] = []
    shot_facts: List[ShotRenderFact] = []
    checklist: List[Dict[str, Any]] = []
    any_caption_burned = False
    for shot, dur in zip(shots, durations):
        image_path = os.path.join(asset_dir, shot.asset_filename)
        out_clip = os.path.join(shots_dir, f"{shot.shot_id}.mp4")
        rendered = False
        if os.path.exists(image_path):
            res = render_shot_clip(
                image_path, work_dir, out_clip,
                shot_id=shot.shot_id, duration_seconds=dur,
                width=width, height=height, caption_text=shot.subtitle_zh,
                focus=shot.focus, zoom=shot.zoom, fps=fps,
            )
            rendered = res.rendered
            any_caption_burned = any_caption_burned or res.caption_burned
            scene_clip_paths.append(out_clip)
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

    # 3. Audio track for the whole timeline.
    audio_path = os.path.join(audio_dir, "narration.wav")
    if azure and any(p for p in shot_audio_paths):
        padded: List[str] = []
        for shot, mp3, dur in zip(shots, shot_audio_paths, durations):
            if not os.path.exists(os.path.join(asset_dir, shot.asset_filename)):
                continue
            seg = os.path.join(work_dir, f"{shot.shot_id}_pad.wav")
            if mp3 and os.path.exists(mp3):
                _pad_audio_to(mp3, seg, dur)
            else:
                generate_silent_audio(seg, duration_seconds=dur)
            padded.append(seg)
        _concat_wavs(padded, audio_path, work_dir)
    else:
        generate_silent_audio(audio_path, duration_seconds=float(sum(rendered_durations)))

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

    # 6. Manifest (real local relative paths only).
    manifest = _build_manifest(
        task_id=task_id, shot_facts=shot_facts, audio_mode=audio_mode,
        caption_mode=caption_mode, duration_seconds=duration_seconds,
        width=width, height=height,
        final_rel=os.path.relpath(final_video_path, output_dir),
        audio_rel=os.path.relpath(audio_path, output_dir),
        subtitle_rel=os.path.relpath(subtitle_path, output_dir),
        scene_rels=[os.path.relpath(p, output_dir) for p in scene_clip_paths],
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
    assert_no_delivery_view_forbidden_tokens(payload)
    return payload

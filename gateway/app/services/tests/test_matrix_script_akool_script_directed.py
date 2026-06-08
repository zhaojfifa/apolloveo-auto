"""Matrix Script — Storyboard Control + Shot Workbench wave PR-4.

Controlled script-directed Akool regeneration: the active/provider-target shot is
generated from a script-derived, role-driven Prompt Builder payload (NOT the
hardcoded DEFAULT_PROMPT), the clip is consumed into final.mp4, and the V1/V2
change explanation is surfaced operator-safe. No network: the Akool call is faked
(capturing the prompt / falling back / writing a real clip). The orchestrator path
is ffmpeg + asset gated; the change-explanation projection is import-light.

Boundary asserted: no DEFAULT_PROMPT for the controlled shot; provider payload
not surfaced; official_publish_ready false; no raw prompt/URL/vendor leak.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import pytest

from gateway.app.services.matrix_script import akool_image_to_video_capability as akool_i2v
from gateway.app.services.matrix_script import ffmpeg_backbone as backbone
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_orchestrator as orch
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod
from gateway.app.services.matrix_script import voiceover_capability
from gateway.app.services.matrix_script.minimal_result_artifact_staging import InMemoryArtifactSink
from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_FFMPEG = ffmpeg_available()
_ASSETS = os.path.isdir(plan_mod.default_asset_dir()) and all(
    os.path.exists(os.path.join(plan_mod.default_asset_dir(), s.asset_filename))
    for s in plan_mod.TOMATO_SHOTS
)
_skip = pytest.mark.skipif(not (_FFMPEG and _ASSETS), reason="ffmpeg/ffprobe or asset pack not present")

_TASK = {"task_id": "ms-pr4", "kind": "matrix_script", "config": {}}


def _enable_akool(monkeypatch) -> None:
    monkeypatch.setattr(orch.akool_i2v, "real_enabled", lambda env=None: True)
    monkeypatch.setattr(orch.akool_i2v, "credentials_present", lambda env=None: True)
    # Silent voiceover (no network TTS) — PR-4 focuses on the provider prompt path.
    monkeypatch.setattr(orch, "_voiceover_synth", lambda *a, **k: voiceover_capability.VoiceoverOutcome(
        voiceover_capability.STATUS_BLOCKED_CREDENTIAL_MISSING, voiceover_capability.PROVIDER_NONE, None, "test"))


def _fake_capture_fail(captured: Dict[str, Any]):
    def _fake(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT, env=None, **kw):
        captured["shot_id"] = shot_id
        captured["prompt"] = prompt
        captured["still_path"] = still_path
        return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_FAILED, None, True, "test_fail")
    return _fake


def _fake_capture_success(captured: Dict[str, Any]):
    def _fake(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT, env=None, **kw):
        captured["shot_id"] = shot_id
        captured["prompt"] = prompt
        # Write a real clip from the still so the orchestrator consumes it as the
        # provider clip (proves the provider clip → final.mp4 path; no real network).
        backbone.generate_with_fallback(still_path, out_clip, duration_seconds=2.0, zoom=backbone.ZOOM_IN)
        return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_SUCCESS, out_clip, True, "")
    return _fake


def _fake_capture_all(captured: Dict[str, Any], *, succeed: bool = True):
    """Multi-shot capture: records every targeted shot's prompt by shot_id. On success it
    writes a real clip per shot so the orchestrator consumes it into final.mp4."""
    captured.setdefault("by_shot", {})

    def _fake(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT, env=None, **kw):
        captured["by_shot"][shot_id] = {"prompt": prompt, "still_path": still_path}
        if succeed:
            backbone.generate_with_fallback(still_path, out_clip, duration_seconds=2.0, zoom=backbone.ZOOM_IN)
            return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_SUCCESS, out_clip, True, "")
        return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_FAILED, None, True, "test_fail")
    return _fake


# --- Multi-shot provider targeting + script-derived prompts (not DEFAULT_PROMPT) --- #
# (Owner batch supersedes the prior one-shot bound: the real-visual storyboard shots are
#  each targeted with a script-derived, role-driven prompt. use_gemini=False keeps the
#  unit tests offline/hermetic — Gemini refinement is exercised in the dedicated module.)

@_skip
def test_multi_shot_targets_are_script_directed_not_default_prompt(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_all(captured, succeed=False))
    orch.run_tomato_real_result(
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, use_gemini=False,
    )
    by = captured["by_shot"]
    # Multi-shot: at least the three real-visual storyboard shots are targeted.
    assert {"shot01", "shot02", "shot03"}.issubset(set(by)), by.keys()
    # Every targeted shot uses a script-derived prompt, never the hardcoded DEFAULT_PROMPT.
    for sid, info in by.items():
        assert info["prompt"] != akool_i2v.DEFAULT_PROMPT
    # Role-driven: shot01 scene-preservation clause; shot02 product-preservation clause.
    assert "preserve scene and background environment continuity" in by["shot01"]["prompt"]
    assert "keep the product's shape, color and texture faithful" in by["shot02"]["prompt"]


@_skip
def test_multi_shot_default_selection_is_real_visual_shots_only(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_all(captured, succeed=False))
    # No active_shot_id → default selection = the real-visual shots (01/02/03); the
    # semantic-reuse shots (04/05) are NOT targeted.
    orch.run_tomato_real_result(
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, use_gemini=False,
    )
    targeted = set(captured["by_shot"])
    assert {"shot01", "shot02", "shot03"}.issubset(targeted)
    assert "shot04" not in targeted and "shot05" not in targeted


# --- Multiple provider clips consumed into final.mp4 + panel evidence -------- #

@_skip
def test_multi_shot_clips_consumed_and_request_panel_evidence(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_all(captured, succeed=True))
    result = orch.run_tomato_real_result(
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, use_gemini=False,
    )
    # final.mp4 exists + publish-ready stays false.
    assert os.path.exists(result.final_video_path) and os.path.getsize(result.final_video_path) > 0
    assert result.official_publish_ready is False
    # >= 2 provider clips consumed into final.mp4 (Owner PASS bar).
    manifest = json.load(open(os.path.join(str(tmp_path), "manifest.json"), encoding="utf-8"))
    per = {r["shot_id"]: r["render_mode"] for r in manifest["per_shot_render"]}
    akool_shots = [sid for sid, m in per.items() if m == orch.RENDER_MODE_AKOOL]
    assert len(akool_shots) >= 2, per
    assert os.path.exists(os.path.join(str(tmp_path), "subtitles", "subtitles.srt"))
    # Capability status carries the multi-shot outcome (operator-safe; no vendor brand).
    cap = result.capability_status["image_to_video"]
    assert cap["status"] == akool_i2v.STATUS_PROVIDER_SUCCESS and cap["succeeded"] is True
    assert cap["multi_shot"] is True
    assert cap["provider_generated_count"] >= 2
    assert cap["script_directed"] is True
    # "AI 生成请求过程" panel present, operator-safe, lists generated vs fallback shots.
    panel = result.capability_status["ai_generation_request_process"]
    assert panel["panel_title_zh"] == "AI 生成请求过程"
    assert len(panel["rows"]) >= 3
    generated_rows = [r for r in panel["rows"] if r["status_code"] == "generated"]
    assert len(generated_rows) >= 2
    # No raw provider URL / api key / raw provider-prompt token in the operator payload.
    payload = orch.tomato_result_to_payload(result)
    blob = str(payload).lower()
    for tok in ("http://", "https://", "x-api-key", "keep the product", "cinematic",
                "realistic lighting", akool_i2v.DEFAULT_PROMPT.lower()):
        assert tok not in blob, "leak %r in payload" % tok


@_skip
def test_other_shots_fall_back_when_provider_fails(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_fail({}))
    result = orch.run_tomato_real_result(
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, active_shot_id="shot02",
        use_gemini=False,
    )
    assert os.path.exists(result.final_video_path)  # final still produced via fallback
    manifest = json.load(open(os.path.join(str(tmp_path), "manifest.json"), encoding="utf-8"))
    modes = {r["render_mode"] for r in manifest["per_shot_render"]}
    # No provider clip consumed (every attempt failed); honest backbone fallback everywhere.
    assert orch.RENDER_MODE_AKOOL not in modes
    assert result.capability_status["image_to_video"]["status"] == akool_i2v.STATUS_PROVIDER_FAILED


# --- V1/V2 change explanation (projection; import-light) -------------------- #

def _staged(cap_extra: Dict[str, Any]) -> Dict[str, Any]:
    image_to_video = {
        "capability": "image_to_video", "status": "provider_success",
        "provider_attempted": True, "succeeded": True,
        "operator_label_zh": "AI 视频生成已生成此镜头",
    }
    image_to_video.update(cap_extra)
    return {
        "task_id": "ms-cce", "kind": "matrix_script",
        "config": {"matrix_script_staged_candidate": {
            "has_result": True, "operator_usable": True, "delivery_candidate": True,
            "preview_url": "/api/matrix-script/ms-cce/tomato-real-result/preview/final.mp4",
            "shot_count": 5, "shot_match_count": 3, "real_visual_count": 3,
            "capability_status": {"image_to_video": image_to_video},
        }},
    }


def test_v1v2_change_explanation_built_for_script_directed() -> None:
    task = _staged({
        "script_directed": True, "provider_target_shot_id": "shot02",
        "material_role": "product_reference", "material_role_label_zh": "产品素材",
        "generation_summary_zh": "小番茄产品特写 · 产品素材 · 缓慢推近",
    })
    view = owv.build_matrix_script_operator_workbench_view(task)
    cce = view["candidate_change_explanation"]
    assert isinstance(cce, dict)
    assert cce["shot_id"] == "shot02"
    assert cce["material_role_label_zh"] == "产品素材"
    assert cce["ai_requirement_summary_zh"] == "小番茄产品特写 · 产品素材 · 缓慢推近"
    assert cce["succeeded"] is True
    assert "AI 视频生成已生成此镜头" in cce["provider_outcome_zh"]


def test_v1v2_change_explanation_none_without_script_directed() -> None:
    # A non-script-directed result (no script_directed flag) → no explanation.
    view = owv.build_matrix_script_operator_workbench_view(_staged({}))
    assert view["candidate_change_explanation"] is None


def test_change_explanation_no_leak() -> None:
    task = _staged({
        "script_directed": True, "provider_target_shot_id": "shot02",
        "material_role": "product_reference", "material_role_label_zh": "产品素材",
        "generation_summary_zh": "小番茄产品特写 · 产品素材 · 缓慢推近",
    })
    view = owv.build_matrix_script_operator_workbench_view(task)  # runs _assert_clean internally
    blob = str(view["candidate_change_explanation"]).lower()
    for tok in owv._FORBIDDEN_TOKENS:
        assert tok not in blob
    for tok in ("http", "://", "cinematic", "keep the product"):
        assert tok not in blob

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


# --- Active-shot provider-target + script-derived prompt (not DEFAULT_PROMPT) --- #

@_skip
def test_active_shot_is_provider_target_and_prompt_is_script_directed(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_fail(captured))
    orch.run_tomato_real_result(_TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, active_shot_id="shot01")
    # The active shot (shot01) — not the hardcoded shot02 — is the provider target.
    assert captured["shot_id"] == "shot01"
    # The prompt is the script-derived Prompt Builder payload, NOT DEFAULT_PROMPT.
    assert captured["prompt"] != akool_i2v.DEFAULT_PROMPT
    # shot01 = scene_reference → its scene-preservation clause is in the provider prompt.
    assert "preserve scene and background environment continuity" in captured["prompt"]


@_skip
def test_default_provider_target_is_product_shot_with_product_prompt(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_fail(captured))
    # No active_shot_id → safe default (shot02, the designated product shot).
    orch.run_tomato_real_result(_TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={})
    assert captured["shot_id"] == "shot02"
    assert captured["prompt"] != akool_i2v.DEFAULT_PROMPT
    # shot02 = product_reference → product-preservation clause in the provider prompt.
    assert "keep the product's shape, color and texture faithful" in captured["prompt"]


# --- Provider clip consumed into final.mp4 + capability evidence ------------- #

@_skip
def test_provider_clip_consumed_into_final_and_capability_evidence(tmp_path, monkeypatch) -> None:
    _enable_akool(monkeypatch)
    captured: Dict[str, Any] = {}
    monkeypatch.setattr(orch.akool_i2v, "generate_shot_clip_akool", _fake_capture_success(captured))
    result = orch.run_tomato_real_result(
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, active_shot_id="shot02"
    )
    # final.mp4 exists + QC ran + publish-ready stays false.
    assert os.path.exists(result.final_video_path) and os.path.getsize(result.final_video_path) > 0
    assert result.official_publish_ready is False
    # The provider clip was consumed for the target shot (render_mode = provider_image_to_video).
    manifest = json.load(open(os.path.join(str(tmp_path), "manifest.json"), encoding="utf-8"))
    per = {r["shot_id"]: r["render_mode"] for r in manifest["per_shot_render"]}
    assert per["shot02"] == orch.RENDER_MODE_AKOOL
    # Subtitles present (sidecar at minimum); other shots fell back honestly.
    assert os.path.exists(os.path.join(str(tmp_path), "subtitles", "subtitles.srt"))
    # Capability status carries operator-safe provider-target evidence.
    cap = result.capability_status["image_to_video"]
    assert cap["status"] == akool_i2v.STATUS_PROVIDER_SUCCESS and cap["succeeded"] is True
    assert cap["provider_target_shot_id"] == "shot02"
    assert cap["material_role"] == "product_reference"
    assert cap["script_directed"] is True
    assert cap.get("generation_summary_zh")
    # No raw provider URL / api key / raw provider-prompt token surfaced in the
    # operator payload. (Internal `artifact://` staged handles + `/files/` preview
    # paths are operator-safe and allowed — the contract's own forbidden-token scan
    # ran inside tomato_result_to_payload and passed.)
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
        _TASK, str(tmp_path), sink=InMemoryArtifactSink(), env={}, active_shot_id="shot02"
    )
    assert os.path.exists(result.final_video_path)  # final still produced via fallback
    manifest = json.load(open(os.path.join(str(tmp_path), "manifest.json"), encoding="utf-8"))
    modes = {r["render_mode"] for r in manifest["per_shot_render"]}
    # No provider clip consumed (it failed); honest backbone fallback for every shot.
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

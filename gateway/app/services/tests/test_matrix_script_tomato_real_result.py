"""Tests for the Matrix Script Tomato Real Result controlled path (PR-A).

Layers:
- pure unit tests for the fixed plan + the operator acceptance gate (no ffmpeg);
- ffmpeg+asset-gated tests for the renderer, orchestrator, and HTTP route.

A fallback-only / missing-real-visual result MUST fail operator acceptance and
MUST NOT become a delivery candidate; the payload must leak no provider/publish
token; official_publish_ready stays false.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import pytest

from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod
from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    InMemoryArtifactSink,
)
from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available
from gateway.app.services.matrix_script.tomato_acceptance_gate import (
    ShotRenderFact,
    compute_tomato_acceptance,
    fallback_only_acceptance,
)

_FFMPEG = ffmpeg_available()
_ASSETS = os.path.isdir(plan_mod.default_asset_dir()) and all(
    os.path.exists(os.path.join(plan_mod.default_asset_dir(), s.asset_filename))
    for s in plan_mod.TOMATO_SHOTS
)
_skip_no_ffmpeg = pytest.mark.skipif(not _FFMPEG, reason="ffmpeg/ffprobe not installed")
_skip_no_assets = pytest.mark.skipif(not _ASSETS, reason="MS-TOMATO-BEACH-001 asset pack not present")


# ---------------------------------------------------------------- plan (pure)

def test_plan_has_five_fixed_shots() -> None:
    assert plan_mod.shot_count() == 5
    assert plan_mod.SCRIPT_TITLE == "海边与圣女果的盛夏约定"
    assert plan_mod.CASE_ID == "MS-TOMATO-BEACH-001"


def test_plan_asset_mapping_matches_launch_instruction() -> None:
    by_id = {s.shot_id: s for s in plan_mod.TOMATO_SHOTS}
    assert by_id["shot01"].asset_filename == "01_beach_hook.png"
    assert by_id["shot02"].asset_filename == "02_tomato_bowl.png"
    assert by_id["shot03"].asset_filename == "03_pick_tomato.png"
    # Shot 04 reuses 03 (品尝爆汁); Shot 05 reuses 02 (CTA).
    assert by_id["shot04"].asset_filename == "03_pick_tomato.png"
    assert by_id["shot05"].asset_filename == "02_tomato_bowl.png"


def test_plan_sources_three_real_two_reuse() -> None:
    real = [s for s in plan_mod.TOMATO_SHOTS if s.source == plan_mod.SOURCE_LOCAL_REAL_ASSET]
    reuse = [s for s in plan_mod.TOMATO_SHOTS if s.source == plan_mod.SOURCE_FALLBACK_SEMANTIC_REUSE]
    assert len(real) == 3 and len(reuse) == 2
    assert all(s.real_visual and s.semantic_match for s in real)
    assert all((not s.real_visual) and (not s.semantic_match) for s in reuse)


# ------------------------------------------------------ acceptance gate (pure)

def _facts(real=3, reuse=2, real_rendered=True, reuse_rendered=True):
    facts = []
    for i in range(real):
        facts.append(ShotRenderFact(f"r{i}", "local_real_asset", real_rendered, real_rendered, real_rendered))
    for i in range(reuse):
        facts.append(ShotRenderFact(f"f{i}", "fallback_semantic_reuse", reuse_rendered, False, False))
    return facts


def test_acceptance_tomato_target_is_partial_pass() -> None:
    acc = compute_tomato_acceptance(_facts())
    assert acc.operator_usable is True
    assert acc.technical_preview is False
    assert acc.delivery_candidate is True
    assert acc.official_publish_ready is False
    assert acc.visual_semantic_match == "partial_pass"
    assert acc.shot_count == 5
    assert acc.shot_match_count == 3
    assert acc.real_visual_count == 3
    assert acc.blocked_reason is None


def test_acceptance_all_five_real_is_pass() -> None:
    acc = compute_tomato_acceptance(_facts(real=5, reuse=0))
    assert acc.visual_semantic_match == "pass"
    assert acc.operator_usable is True


def test_acceptance_fallback_only_fails_and_blocks() -> None:
    # only reuse shots rendered, no real visual → fallback-only
    acc = compute_tomato_acceptance(_facts(real=0, reuse=3))
    assert acc.operator_usable is False
    assert acc.technical_preview is True
    assert acc.delivery_candidate is False
    assert acc.visual_semantic_match == "failed"
    assert acc.real_visual_count == 0
    assert acc.blocked_reason == "fallback_only_or_missing_real_visuals"


def test_acceptance_two_real_below_bar_not_usable() -> None:
    acc = compute_tomato_acceptance(_facts(real=2, reuse=2))
    assert acc.real_visual_count == 2
    assert acc.shot_match_count == 2
    assert acc.operator_usable is False  # needs >= 3 matches
    assert acc.blocked_reason == "fallback_only_or_missing_real_visuals"


def test_explicit_fallback_only_helper() -> None:
    acc = fallback_only_acceptance(shot_count=5)
    assert acc.operator_usable is False and acc.visual_semantic_match == "failed"


# --------------------------------------------------- orchestrator (e2e, gated)

@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_produces_operator_usable_tomato(tmp_path) -> None:
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
        run_tomato_real_result,
        tomato_result_to_payload,
    )

    task = {"task_id": "tomato-e2e", "kind": "matrix_script"}
    sink = InMemoryArtifactSink()
    # no Azure env → honest silent fallback
    res = run_tomato_real_result(task, str(tmp_path), sink=sink, env={})
    acc = res.acceptance
    assert acc["operator_usable"] is True
    assert acc["technical_preview"] is False
    assert acc["visual_semantic_match"] == "partial_pass"
    assert acc["shot_count"] == 5
    assert acc["real_visual_count"] == 3
    assert acc["shot_match_count"] == 3
    assert acc["official_publish_ready"] is False
    assert res.audio_mode == "silent_fallback"
    assert os.path.exists(res.final_video_path)
    assert os.path.getsize(res.final_video_path) > 0
    assert res.duration_seconds > 0

    # Backbone integration: scene clips render through the ffmpeg backbone +
    # the composed final.mp4 carries an ffprobe QC verdict (operator-safe).
    assert res.scene_engine == "ffmpeg_backbone"
    assert res.qc_passed is True
    assert res.qc_resolution == "1080x1920"

    payload = tomato_result_to_payload(res)
    assert payload["storage_scope"] == "artifact_staged"
    assert payload["delivery_candidate"] is True
    assert payload["generation_provider"] == "none"
    assert payload["scene_engine"] == "ffmpeg_backbone"
    assert payload["backbone_qc_passed"] is True
    assert payload["backbone_qc_resolution"] == "1080x1920"
    assert payload["official_publish_ready"] is False
    blob = str(payload).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url",
                  "publish_url", "publish_status", "model_id", "credit",
                  "provider_task_id", "http://", "https://"):
        assert token not in blob


@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_renders_real_frames_9x16(tmp_path) -> None:
    from gateway.app.services.matrix_script.simple_scene_renderer import probe_duration_seconds
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import run_tomato_real_result

    res = run_tomato_real_result(
        {"task_id": "tomato-frames", "kind": "matrix_script"}, str(tmp_path),
        sink=InMemoryArtifactSink(), env={},
    )
    # Operator-visible scene clips now render through the ffmpeg backbone at its
    # deterministic 1080×1920 spec (Owner-approved backbone integration).
    assert (res.width, res.height) == (1080, 1920)
    # 5 shots × 4s silent fallback ≈ 20s
    assert probe_duration_seconds(res.final_video_path) >= 15.0


@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_backbone_manifest_qc_and_per_shot_render(tmp_path) -> None:
    """The operator-visible manifest carries backbone evidence + an ffprobe QC verdict."""
    import json
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
        run_tomato_real_result,
    )

    res = run_tomato_real_result(
        {"task_id": "tomato-backbone", "kind": "matrix_script"}, str(tmp_path),
        sink=InMemoryArtifactSink(), env={},
    )
    manifest = json.load(open(os.path.join(str(tmp_path), "manifest.json")))
    assert manifest["scene_engine"] == "ffmpeg_backbone"
    assert manifest["resolution"] == "1080x1920"
    # every shot rendered through the backbone (proxy or static-still fallback)
    assert len(manifest["per_shot_render"]) == 5
    assert all(
        r["render_mode"] in ("ffmpeg_backbone_proxy", "ffmpeg_backbone_static_still")
        for r in manifest["per_shot_render"]
    )
    # ffprobe QC verdict on the composed operator-visible final.mp4
    qc = manifest["qc"]
    assert qc["passed"] is True
    assert qc["resolution"] == "1080x1920"
    assert qc["codec"] == "h264"
    assert abs(float(qc["fps"]) - 30.0) < 0.01
    assert qc["official_publish_ready"] is False
    assert manifest["backbone"]["is_generative"] is False
    # no provider/publish leakage in the operator-safe manifest
    blob = json.dumps(manifest, ensure_ascii=False).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url",
                  "publish_url", "publish_status", "model_id", "credit"):
        assert token not in blob


@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_backbone_consumes_replacement_material(tmp_path) -> None:
    """An uploaded/replacement material is rendered through the backbone + reported consumed."""
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
        run_tomato_real_result,
    )

    # Reuse a real asset as a stand-in resolvable uploaded image override for shot04.
    repl = os.path.join(plan_mod.default_asset_dir(), "04_eat_tomato.png")
    if not os.path.exists(repl):
        repl = os.path.join(plan_mod.default_asset_dir(), "02_tomato_bowl.png")
    overrides = {
        "shot04": {
            "local_path": repl, "material_kind": "image",
            "material_name": os.path.basename(repl),
            "material_ref": "msmaterial://t/shot04/" + os.path.basename(repl),
            "material_source": "operator_upload",
        }
    }
    res = run_tomato_real_result(
        {"task_id": "tomato-backbone-mat", "kind": "matrix_script"}, str(tmp_path),
        sink=InMemoryArtifactSink(), env={}, material_overrides=overrides,
    )
    assert "shot04" in res.consumed_material_shot_ids
    assert res.scene_engine == "ffmpeg_backbone"
    assert res.qc_passed is True
    assert os.path.getsize(res.final_video_path) > 0


@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_voiceover_status_and_capability_status_no_creds(tmp_path) -> None:
    """With no TTS credentials, voiceover is honestly blocked + capability status is operator-safe."""
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
        run_tomato_real_result, tomato_result_to_payload,
    )

    res = run_tomato_real_result(
        {"task_id": "tomato-voice", "kind": "matrix_script"}, str(tmp_path),
        sink=InMemoryArtifactSink(), env={},
    )
    # honest: no fake voiceover — silent fallback + blocked status
    assert res.voiceover_status == "blocked_credential_missing"
    assert res.audio_mode == "silent_fallback"
    cap = res.capability_status
    assert cap["voiceover"]["status"] == "blocked_credential_missing"
    assert cap["voiceover"]["generated"] is False
    # image_to_video uses the Akool capability taxonomy; no flag/creds → credential_missing
    assert cap["image_to_video"]["status"] == "credential_missing"
    assert cap["subtitles"]["status"] == "generated"   # burned captions
    assert cap["bgm"]["status"] == "not_selected"
    # final video still playable + publish-ready stays false
    assert os.path.getsize(res.final_video_path) > 0
    assert res.acceptance["official_publish_ready"] is False
    # operator-safe: no provider/vendor/secret leak in payload capability status
    payload = tomato_result_to_payload(res)
    assert payload["voiceover_status"] == "blocked_credential_missing"
    blob = str(payload["capability_status"]).lower()
    for token in ("azure", "kling", "runway", "veo", "akool", "speech_key", "api_key"):
        assert token not in blob


@_skip_no_ffmpeg
@_skip_no_assets
def test_orchestrator_composes_real_voiceover_when_tts_available(tmp_path, monkeypatch) -> None:
    """When a TTS path yields audio, it is composed into final.mp4 (real, not faked)."""
    import subprocess
    from gateway.app.services.matrix_script import tomato_real_result_orchestrator as orch
    from gateway.app.services.matrix_script import voiceover_capability as vc

    def fake_synth(text, out_path, *, env, voice):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=18",
             "-ar", "44100", "-ac", "1", out_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        return vc.VoiceoverOutcome(vc.STATUS_GENERATED, vc.PROVIDER_EDGE, out_path)

    monkeypatch.setattr(orch, "_voiceover_synth", fake_synth)
    res = orch.run_tomato_real_result(
        {"task_id": "tomato-voice-ok", "kind": "matrix_script"}, str(tmp_path),
        sink=InMemoryArtifactSink(), env={},
    )
    assert res.voiceover_status == "generated"
    assert res.audio_mode == "edge_tts"
    assert res.capability_status["voiceover"]["operator_label_zh"] == "旁白已生成"
    # the composed final carries a non-silent audio stream
    vol = subprocess.run(
        ["ffmpeg", "-i", res.final_video_path, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    means = [l for l in vol.stderr.splitlines() if "mean_volume" in l]
    assert means, "no volumedetect output"
    db = float(means[0].split("mean_volume:")[1].split("dB")[0].strip())
    assert db > -80.0  # real narration, not pure silence


def test_operator_workbench_view_surfaces_capability_status() -> None:
    """The operator workbench view passes capability status through (read-only)."""
    from gateway.app.services.matrix_script.operator_workbench_view import (
        build_matrix_script_operator_workbench_view,
    )

    staged = {
        "has_result": True, "operator_usable": True, "delivery_candidate": True,
        "visual_semantic_match": "partial_pass", "shot_count": 5,
        "real_visual_count": 3, "shot_match_count": 3,
        "preview_url": "/api/matrix-script/t/preview-version/V1/final.mp4",
        "voiceover_status": "blocked_credential_missing",
        "capability_status": {
            "voiceover": {"capability": "voiceover", "status": "blocked_credential_missing",
                          "generated": False, "operator_label_zh": "旁白未生成 · 缺少语音凭证（已保留静音）"},
            "subtitles": {"capability": "subtitles", "status": "generated",
                          "operator_label_zh": "字幕已烧录"},
        },
    }
    task = {"task_id": "t", "kind": "matrix_script",
            "config": {"matrix_script_staged_candidate": staged}}
    view = build_matrix_script_operator_workbench_view(task)
    assert view["voiceover_status"] == "blocked_credential_missing"
    assert view["capability_status"]["subtitles"]["status"] == "generated"
    assert view["capability_status"]["voiceover"]["generated"] is False


def test_orchestrator_raises_without_assets(tmp_path) -> None:
    if not _FFMPEG:
        pytest.skip("ffmpeg not installed")
    from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
        TomatoRealResultError,
        run_tomato_real_result,
    )

    empty_assets = tmp_path / "empty_assets"
    empty_assets.mkdir()
    with pytest.raises(TomatoRealResultError):
        run_tomato_real_result(
            {"task_id": "no-assets", "kind": "matrix_script"}, str(tmp_path / "out"),
            sink=InMemoryArtifactSink(), env={}, asset_dir=str(empty_assets),
        )


# --------------------------------------------------------------- route (gated)

class _StubRepo:
    def __init__(self, tasks: Dict[str, Dict[str, Any]]):
        self._tasks = tasks
        self.mutations: list = []

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def create(self, task):  # pragma: no cover
        self.mutations.append("create"); raise NotImplementedError

    def update(self, task_id, patch):  # pragma: no cover
        self.mutations.append("update"); raise NotImplementedError

    def list(self):  # pragma: no cover
        return list(self._tasks.values())


def _matrix_task(task_id="ms-tomato-1"):
    return {"task_id": task_id, "kind": "matrix_script"}


def _build(repo, tmp_path, monkeypatch):
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover
        return None
    from gateway.app.deps import get_task_repository
    from gateway.app.routers import matrix_script_tomato_real_result as route_module

    monkeypatch.setattr(route_module, "resolve_tomato_output_dir", lambda task_id: str(tmp_path / task_id))
    monkeypatch.setattr(route_module, "build_tomato_sink", lambda task_id: InMemoryArtifactSink())
    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(route_module.api_router)
    return TestClient(app)


def test_route_non_matrix_rejected(tmp_path, monkeypatch) -> None:
    client = _build(_StubRepo({"hf": {"task_id": "hf", "kind": "hot_follow"}}), tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    assert client.post("/api/matrix-script/hf/tomato-real-result").status_code == 400


def test_route_unknown_task_404(tmp_path, monkeypatch) -> None:
    client = _build(_StubRepo({}), tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    assert client.post("/api/matrix-script/missing/tomato-real-result").status_code == 404


@_skip_no_ffmpeg
@_skip_no_assets
def test_route_returns_gated_payload_and_preview(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"ms-tomato-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    resp = client.post("/api/matrix-script/ms-tomato-1/tomato-real-result")
    assert resp.status_code == 200
    body = resp.json()
    assert body["operator_usable"] is True
    assert body["technical_preview"] is False
    assert body["visual_semantic_match"] == "partial_pass"
    assert body["real_visual_count"] == 3
    assert body["shot_match_count"] == 3
    assert body["delivery_candidate"] is True
    assert body["official_publish_ready"] is False
    assert body["preview_url"] == "/api/matrix-script/ms-tomato-1/tomato-real-result/preview/final.mp4"
    blob = str(body).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url",
                  "publish_url", "publish_status", "model_id", "credit", "http://", "https://"):
        assert token not in blob
    assert repo.mutations == []
    # preview streams the staged final.mp4
    pv = client.get(body["preview_url"])
    assert pv.status_code == 200
    assert pv.headers.get("content-type", "").startswith("video/mp4")
    assert len(pv.content) > 0


def test_route_ffmpeg_missing_503_no_fake(tmp_path, monkeypatch) -> None:
    from gateway.app.services.matrix_script import tomato_real_result_orchestrator as orch
    monkeypatch.setattr(orch, "ffmpeg_available", lambda: False)
    repo = _StubRepo({"ms-tomato-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    resp = client.post("/api/matrix-script/ms-tomato-1/tomato-real-result")
    assert resp.status_code == 503
    assert not os.path.exists(str(tmp_path / "ms-tomato-1" / "final" / "final.mp4"))
    assert repo.mutations == []

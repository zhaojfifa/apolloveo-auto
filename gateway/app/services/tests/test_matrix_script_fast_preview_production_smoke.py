"""Matrix Script Fast Preview Production Smoke (runtime acceptance).

Proves the merged ffmpeg-backbone fast-preview path is operator-CONSUMABLE end to end,
using ONLY existing public service/projection functions (read-only — no runtime change):

    run_minimal_result_loop(shot_images=...)   # backbone engaged on a tomato fixture
      → MatrixScriptMinimalResultSummary
      → minimal_result_summary_to_record
      → minimal_result_record_to_operator_projection / _delivery_projection
      → operator_projection_to_dict / delivery_projection_to_dict (closed, UI/delivery-safe)

Verifies: final.mp4 + manifest + subtitles + audio produced; ffprobe QC + backbone
evidence on the manifest; the existing operator + delivery projections consume the
artifacts; the color-card fallback path is preserved; official_publish_ready stays false;
no forbidden-token leakage. Real-render cases skip when ffmpeg/ffprobe are absent (no fake
final.mp4 is ever produced).

This is an acceptance smoke. It modifies no runtime; it does not thread shot_images through
the operator service entry (that would touch minimal_result_service.py — reported as a
scope-expansion decision, not done here).
"""
from __future__ import annotations

import json
import os

import pytest

from gateway.app.services.matrix_script import ffmpeg_backbone as backbone
from gateway.app.services.matrix_script.minimal_result_loop import (
    SCENE_STRATEGY_BACKBONE,
    RENDER_MODE_COLOR_CARD,
    run_minimal_result_loop,
)
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultSummary,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    minimal_result_summary_to_record,
)
from gateway.app.services.matrix_script.minimal_result_projection import (
    minimal_result_record_to_operator_projection,
    minimal_result_record_to_delivery_projection,
    operator_projection_to_dict,
    delivery_projection_to_dict,
)
from gateway.app.services.matrix_script.shot_plan_builder import build_shot_plan
from gateway.app.services.matrix_script.simple_scene_renderer import probe_duration_seconds

_FFMPEG = backbone.ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG, reason="ffmpeg/ffprobe not installed; production smoke skipped (no fake final.mp4)"
)

_TOMATO_DIR = "assets/matrix_script_assets/MS-TOMATO-BEACH-001"


def _tomato_outline():
    return {
        "hook": "夏日番茄，鲜甜一口",
        "body": ["切开展示新鲜番茄", "递向镜头品尝特写", "沙滩生活场景"],
        "cta": "评论区告诉我你的需求",
    }


def _summary_from_output(output, *, task_id):
    m = output.manifest
    return MatrixScriptMinimalResultSummary(
        task_id=task_id,
        final_video_path=output.final_video_path,
        manifest_path=output.manifest_path,
        subtitles_path=output.subtitle_path,
        audio_path=output.audio_path,
        shot_count=int(m["shot_count"]),
        duration_seconds=float(probe_duration_seconds(output.final_video_path)),
        generation_provider=str(m["generation_provider"]),
        scene_strategy=str(m["scene_strategy"]),
        audio_strategy=str(m["audio_strategy"]),
    )


@_skip_no_ffmpeg
def test_backbone_fast_preview_is_operator_consumable(tmp_path):
    # 1. real tomato fixture; map available stills to the first shots, leave one without.
    outline = _tomato_outline()
    plan = build_shot_plan(outline, task_id="smoke-tomato", target_duration_seconds=8.0)
    shot_ids = [s.shot_id for s in plan.shots]
    stills = {}
    for sid, name in zip(shot_ids, ["02_tomato_bowl.png", "04_eat_tomato.png", "03_pick_tomato.png"]):
        p = os.path.join(_TOMATO_DIR, name)
        if os.path.isfile(p):
            stills[sid] = p
    assert stills, "tomato benchmark stills missing"

    out_dir = str(tmp_path / "out")
    os.makedirs(out_dir, exist_ok=True)

    # 2. run the existing loop with shot_images -> backbone engaged.
    output = run_minimal_result_loop(
        outline, out_dir, task_id="smoke-tomato", target_duration_seconds=8.0, shot_images=stills,
    )

    # 3. real artifacts exist.
    assert os.path.exists(output.final_video_path) and os.path.getsize(output.final_video_path) > 0
    assert os.path.exists(output.manifest_path)
    assert os.path.exists(output.subtitle_path)
    assert os.path.exists(output.audio_path)
    m = output.manifest
    assert m["scene_strategy"] == SCENE_STRATEGY_BACKBONE
    assert m["qc"]["passed"] is True and m["qc"]["resolution"] == "1080x1920"
    assert m["backbone"]["is_generative"] is False
    assert m["backbone"]["official_publish_ready"] is False
    # color-card fallback preserved (at least one shot had no still).
    assert any(r["render_mode"] == RENDER_MODE_COLOR_CARD for r in m["per_shot_render"])

    # 4. existing operator + delivery projections CONSUME the produced artifacts (read-only).
    #    NOTE (finding): the projection's closed key set surfaces the artifact PATHS +
    #    publish-readiness, but does NOT expose scene_strategy/qc as first-class fields;
    #    the backbone evidence is operator-referenceable via the manifest (manifest_path).
    summary = _summary_from_output(output, task_id="smoke-tomato")
    record = minimal_result_summary_to_record(summary)

    op = operator_projection_to_dict(minimal_result_record_to_operator_projection(record))
    assert op["has_final_video"] is True and op["final_video_path"] == output.final_video_path
    assert op["has_manifest"] is True and op["manifest_path"] == output.manifest_path
    assert op["has_subtitles"] is True and op["has_audio"] is True
    assert op["shot_count"] == m["shot_count"]
    assert op["publish_ready_candidate"] is True   # local pack complete + provider-free
    assert op["official_publish_ready"] is False    # delivery truth unchanged

    dv = delivery_projection_to_dict(minimal_result_record_to_delivery_projection(record))
    assert dv["has_final_video"] is True and dv["official_publish_ready"] is False

    # the backbone strategy + QC fact is referenceable via the surfaced manifest path.
    with open(output.manifest_path, encoding="utf-8") as fh:
        referenced = json.load(fh)
    assert referenced["scene_strategy"] == SCENE_STRATEGY_BACKBONE
    assert referenced["qc"]["passed"] is True

    # 5. no provider/secret/vendor leakage in the operator-visible payloads.
    blob = (json.dumps(op, ensure_ascii=False) + json.dumps(dv, ensure_ascii=False)).lower()
    for forbidden in ("akool", "provider_url", "vendor", "model_id", "credit", "kling", "runway", "veo"):
        assert forbidden not in blob


@_skip_no_ffmpeg
def test_legacy_color_card_still_operator_consumable(tmp_path):
    # No shot_images -> legacy color-card result still surfaces through the same projection.
    outline = _tomato_outline()
    out_dir = str(tmp_path / "out")
    os.makedirs(out_dir, exist_ok=True)
    output = run_minimal_result_loop(outline, out_dir, task_id="smoke-legacy", target_duration_seconds=8.0)
    assert output.manifest["scene_strategy"] == "ffmpeg_color_card"
    assert "qc" not in output.manifest  # legacy path adds no backbone evidence

    summary = _summary_from_output(output, task_id="smoke-legacy")
    op = operator_projection_to_dict(
        minimal_result_record_to_operator_projection(minimal_result_summary_to_record(summary))
    )
    assert op["has_final_video"] is True and op["has_manifest"] is True
    assert op["official_publish_ready"] is False

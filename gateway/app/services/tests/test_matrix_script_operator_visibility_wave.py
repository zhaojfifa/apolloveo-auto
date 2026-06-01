"""Matrix Script Operator Visibility Wave tests (Phase 3 PR-14R).

Covers:
- `minimal_result_trace.py` — closed 6-step execution trace.
- `minimal_result_delivery_view.py` — Delivery local read-only result block.
- `task_publish_hub.html` — Delivery local-result block (static).
- `task_workbench.html` — execution-trace rendering (static).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    DELIVERY_NOTE,
    DeliveryViewError,
    assert_no_delivery_view_forbidden_tokens,
    derive_matrix_script_minimal_result_delivery_block,
    minimal_result_surface_view_to_delivery_block,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    minimal_result_summary_to_record,
)
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultSummary,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    minimal_result_record_to_surface_view,
    minimal_result_surface_view_to_dict,
)
from gateway.app.services.matrix_script.minimal_result_trace import (
    STATUS_DONE,
    STATUS_PENDING,
    TRACE_STATUSES,
    build_minimal_result_trace,
    trace_step_labels,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
_PUBLISH_HUB = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"

_REQUIRED_STEPS = ["shot_plan", "scene_clips", "audio", "subtitles", "assembly", "surface"]


def _surface_dict(**overrides):
    summary = MatrixScriptMinimalResultSummary(
        task_id=overrides.pop("task_id", "ms-vis-1"),
        final_video_path=overrides.pop("final_video_path", "/ws/r/final/final.mp4"),
        manifest_path="/ws/r/manifest.json",
        subtitles_path="/ws/r/subtitles/subtitles.srt",
        audio_path="/ws/r/audio/narration.wav",
        shot_count=overrides.pop("shot_count", 6),
        duration_seconds=overrides.pop("duration_seconds", 19.96),
        generation_provider="none",
        scene_strategy="ffmpeg_color_card",
        audio_strategy="silent_fallback",
    )
    return minimal_result_surface_view_to_dict(minimal_result_record_to_surface_view(minimal_result_summary_to_record(summary)))


# ---------------------------------------------------------------------------
# execution trace (acceptance 6,7,8)
# ---------------------------------------------------------------------------


def test_trace_has_required_steps_in_order() -> None:
    trace = build_minimal_result_trace(_surface_dict())
    assert [s["step"] for s in trace] == _REQUIRED_STEPS


def test_trace_all_done_when_result_present() -> None:
    trace = build_minimal_result_trace(_surface_dict())
    assert all(s["status"] == STATUS_DONE for s in trace)
    assert all(s["status"] in TRACE_STATUSES for s in trace)


def test_trace_pending_when_no_result() -> None:
    assert all(s["status"] == STATUS_PENDING for s in build_minimal_result_trace({"has_result": False}))
    assert all(s["status"] == STATUS_PENDING for s in build_minimal_result_trace(None))


def test_trace_labels_present() -> None:
    labels = trace_step_labels()
    for expected in ("生成镜头计划", "生成场景片段", "生成音频", "生成字幕", "合成成片", "生成结果视图"):
        assert expected in labels


# ---------------------------------------------------------------------------
# delivery view (acceptance 1-5)
# ---------------------------------------------------------------------------


def test_delivery_block_from_task_config() -> None:
    task = {"task_id": "t", "kind": "matrix_script", "config": {"matrix_script_minimal_result": _surface_dict()}}
    block = derive_matrix_script_minimal_result_delivery_block(task)
    assert block["has_result"] is True
    assert block["final_video_label"] == "本地最小成片"
    assert block["result_status"] == "generated"
    assert block["final_video_path"].endswith("final.mp4")
    assert block["storage_scope"] == "local_workspace"
    assert block["official_publish_ready"] is False
    assert block["delivery_note"] == DELIVERY_NOTE
    assert "尚未进入正式交付存储" in block["delivery_note"]


def test_delivery_block_empty_without_config() -> None:
    assert derive_matrix_script_minimal_result_delivery_block({"config": {}}) == {"has_result": False}
    assert derive_matrix_script_minimal_result_delivery_block("x") == {"has_result": False}


def test_delivery_block_official_publish_ready_pinned_false() -> None:
    lying = dict(_surface_dict())
    lying["official_publish_ready"] = True
    task = {"config": {"matrix_script_minimal_result": lying}}
    assert derive_matrix_script_minimal_result_delivery_block(task)["official_publish_ready"] is False


def test_delivery_block_no_forbidden_keys_or_tokens() -> None:
    block = derive_matrix_script_minimal_result_delivery_block(
        {"config": {"matrix_script_minimal_result": _surface_dict()}}
    )
    for forbidden_key in ("publish_url", "publish_status", "download_url", "artifact_key", "r2_key", "final_video_key"):
        assert forbidden_key not in block
    blob = json.dumps(block, ensure_ascii=False).lower()
    for token in ("akool", "provider", "vendor", "model_id", "credit", "http://", "https://"):
        assert token not in blob


def test_delivery_view_from_surface_view_object() -> None:
    summary = MatrixScriptMinimalResultSummary(
        task_id="t", final_video_path="/ws/r/final/final.mp4", manifest_path="/ws/r/manifest.json",
        subtitles_path="/ws/r/subtitles/subtitles.srt", audio_path="/ws/r/audio/narration.wav",
        shot_count=6, duration_seconds=19.96, generation_provider="none",
        scene_strategy="ffmpeg_color_card", audio_strategy="silent_fallback",
    )
    view = minimal_result_record_to_surface_view(minimal_result_summary_to_record(summary))
    block = minimal_result_surface_view_to_delivery_block(view)
    assert block["has_result"] is True and block["official_publish_ready"] is False


def test_delivery_guard_rejects_publish_url() -> None:
    with pytest.raises(DeliveryViewError):
        assert_no_delivery_view_forbidden_tokens({"publish_url": "x"})


# ---------------------------------------------------------------------------
# Delivery template (publish_hub) static checks (acceptance 1-5, 10)
# ---------------------------------------------------------------------------


def test_publish_hub_has_local_result_block() -> None:
    src = _PUBLISH_HUB.read_text(encoding="utf-8")
    assert 'data-role="matrix-script-dc-local-result"' in src
    assert "{% if ms_local_result.has_result %}" in src
    assert "该结果尚未进入正式交付存储，不能作为正式发布文件" in src
    assert 'data-role="ms-dc-local-result-scope"' in src
    assert 'data-role="ms-dc-local-result-publish-ready"' in src


def test_publish_hub_local_block_gated_to_matrix_script_and_leak_free() -> None:
    src = _PUBLISH_HUB.read_text(encoding="utf-8")
    ms_gate = src.find('ms_pub.is_matrix_script')
    anchor = src.find('data-role="matrix-script-dc-local-result"')
    assert ms_gate != -1 and anchor != -1 and ms_gate < anchor
    gate = src.find("{% if ms_local_result.has_result %}")
    end = src.find("{% endif %}", anchor)
    block = src[gate:end].lower()
    for token in ("akool", "provider", "vendor", "model_id", "credit", "publish_url", "publish_status", "download_url", "artifact_key", "r2_key", ".mp4", "http://", "https://"):
        assert token not in block, f"DC local-result block leaks '{token}'"


# ---------------------------------------------------------------------------
# Workbench template execution-trace static checks (acceptance 6-8, 10)
# ---------------------------------------------------------------------------


def test_workbench_has_trace_container_and_steps() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    assert 'data-role="ms-minimal-result-trace"' in src
    assert "renderTrace(" in src
    assert "var TRACE_STEPS" in src
    for label in ("生成镜头计划", "生成场景片段", "生成音频", "生成字幕", "合成成片", "生成结果视图"):
        assert label in src
    for step in _REQUIRED_STEPS:
        assert f"'{step}'" in src


def test_workbench_trace_is_inside_matrix_script_action_block_and_leak_free() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    action = src.find('data-role="matrix-script-minimal-result-action"')
    trace = src.find('data-role="ms-minimal-result-trace"')
    da = src.find('ops_workbench_panel.panel_kind == "digital_anchor"')
    ms = src.find('ops_workbench_panel.panel_kind == "matrix_script"')
    assert ms != -1 and action != -1 and trace != -1
    assert ms < action < trace < da  # inside the matrix_script branch, before digital_anchor


# ---------------------------------------------------------------------------
# trace forbidden-token guard
# ---------------------------------------------------------------------------


def test_trace_serialization_is_leak_free() -> None:
    blob = json.dumps(build_minimal_result_trace(_surface_dict()), ensure_ascii=False).lower()
    for token in ("akool", "provider", "vendor", "model_id", "credit", "publish_url", "publish_status", "http://", "https://"):
        assert token not in blob

"""Delivery render-path fix tests (PR-185).

The publish template's `task` is a projected `detail` that cannot reach
`config.matrix_script_*`. The fix surfaces the local-result + staged candidate
through `ms_pub` (the matrix_script publish render-data, which gets the RAW
task). These tests assert the render-data carries the candidate and the
template reads `ms_pub.*`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    DeliveryViewError,
    derive_matrix_script_staged_candidate_block,
)
from gateway.app.services.matrix_script.publish_hub_render_data import (
    derive_matrix_script_publish_hub_render_data,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PUBLISH_HUB = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


def _staged_candidate_dict():
    return {
        "has_result": True,
        "line_id": "matrix_script",
        "final_video_label": "本地最小成片",
        "storage_scope": "artifact_staged",
        "delivery_candidate": True,
        "official_publish_ready": False,
        "generation_provider": "none",
        "final_video_artifact_ref": "artifact://matrix_script/t/final/final.mp4",
        "manifest_artifact_ref": "artifact://matrix_script/t/manifest/manifest.json",
        "subtitles_artifact_ref": "artifact://matrix_script/t/subtitles/subtitles.srt",
        "audio_artifact_ref": "artifact://matrix_script/t/audio/narration.wav",
        "scene_clip_count": 6,
        "preview_url": "/api/matrix-script/t/real-trial/preview/final.mp4",
        "delivery_note": "该结果已暂存为交付候选（artifact staged），但尚未正式发布。",
    }


def _local_result_dict():
    return {
        "has_result": True,
        "final_video_label": "本地最小成片",
        "result_status": "generated",
        "final_video_path": "/ws/r/final/final.mp4",
        "duration_seconds": 19.96,
        "shot_count": 6,
        "storage_scope": "local_workspace",
        "official_publish_ready": False,
        "operator_note": "已生成本地最小成片，尚未进入正式交付存储",
    }


def _task(**config):
    return {"task_id": "t", "kind": "matrix_script", "config": dict(config)}


# ---------------------------------------------------------------------------
# render-data carries the candidate from RAW task config
# ---------------------------------------------------------------------------


def test_render_data_surfaces_staged_candidate() -> None:
    task = _task(matrix_script_staged_candidate=_staged_candidate_dict())
    rd = derive_matrix_script_publish_hub_render_data(task)
    sc = rd["staged_candidate"]
    assert sc["has_result"] is True
    assert sc["storage_scope"] == "artifact_staged"
    assert sc["official_publish_ready"] is False
    assert sc["preview_url"] == "/api/matrix-script/t/real-trial/preview/final.mp4"
    assert str(sc["final_video_artifact_ref"]).startswith("artifact://")


def test_render_data_surfaces_local_result() -> None:
    task = _task(matrix_script_minimal_result=_local_result_dict())
    rd = derive_matrix_script_publish_hub_render_data(task)
    lr = rd["local_result"]
    assert lr["has_result"] is True
    assert lr["storage_scope"] == "local_workspace"
    assert lr["official_publish_ready"] is False


def test_render_data_empty_candidates_without_config() -> None:
    rd = derive_matrix_script_publish_hub_render_data(_task())
    assert rd["staged_candidate"] == {"has_result": False}
    assert rd["local_result"] == {"has_result": False}


def test_render_data_empty_for_non_matrix_task() -> None:
    rd = derive_matrix_script_publish_hub_render_data({"task_id": "h", "kind": "hot_follow"})
    assert rd == {}


# ---------------------------------------------------------------------------
# staged-candidate reader discipline
# ---------------------------------------------------------------------------


def test_staged_candidate_block_pins_official_publish_ready_false() -> None:
    lying = _staged_candidate_dict(); lying["official_publish_ready"] = True
    block = derive_matrix_script_staged_candidate_block(_task(matrix_script_staged_candidate=lying))
    assert block["official_publish_ready"] is False


def test_staged_candidate_block_empty_and_leak_free() -> None:
    assert derive_matrix_script_staged_candidate_block(_task()) == {"has_result": False}
    assert derive_matrix_script_staged_candidate_block("x") == {"has_result": False}
    # forbidden token in a persisted candidate → empty (never breaks render)
    bad = _staged_candidate_dict(); bad["final_video_artifact_ref"] = "served by akool"
    assert derive_matrix_script_staged_candidate_block(_task(matrix_script_staged_candidate=bad)) == {"has_result": False}


def test_staged_candidate_block_no_publish_or_provider_leak() -> None:
    block = derive_matrix_script_staged_candidate_block(_task(matrix_script_staged_candidate=_staged_candidate_dict()))
    blob = json.dumps(block, ensure_ascii=False).lower()
    for token in ("provider_url", "temporary_url", "publish_url", "publish_status", "download_url", "akool", "model_id", "credit"):
        assert token not in blob


# ---------------------------------------------------------------------------
# template now reads ms_pub.* (not task.config.*)
# ---------------------------------------------------------------------------


def test_template_reads_render_data_keys() -> None:
    src = _PUBLISH_HUB.read_text(encoding="utf-8")
    assert "{% set ms_local_result = ms_pub.local_result or {} %}" in src
    assert "{% set ms_staged = ms_pub.staged_candidate or {} %}" in src
    # old raw-config reads removed
    assert "(task.config or {}).matrix_script_minimal_result" not in src
    assert "(task.config or {}).matrix_script_staged_candidate" not in src
    # blocks + preview link still present
    assert 'data-role="matrix-script-dc-staged-candidate"' in src
    assert 'data-role="ms-dc-staged-preview"' in src

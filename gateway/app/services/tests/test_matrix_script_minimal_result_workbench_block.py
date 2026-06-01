"""Matrix Script minimal result Workbench block tests (Phase 3 PR-9R).

Covers the architecture-to-operator-result bridge:
- ``minimal_result_workbench_block.py`` (surface view → block; task-config
  wiring adapter; leakage guards), and
- the small read-only block wired into ``task_workbench.html`` (static checks).

Pure unit + static template assertions (no ffmpeg, no Jinja render).
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from gateway.app.services.matrix_script import (
    minimal_result_workbench_block as block_module,
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
from gateway.app.services.matrix_script.minimal_result_workbench_block import (
    WorkbenchResultBlockError,
    assert_no_workbench_block_forbidden_tokens,
    derive_matrix_script_minimal_result_workbench_block,
    minimal_result_surface_view_to_workbench_block,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _surface_view():
    summary = MatrixScriptMinimalResultSummary(
        task_id="ms-demo-1",
        final_video_path="/ws/matrix_script_result/final/final.mp4",
        manifest_path="/ws/matrix_script_result/manifest.json",
        subtitles_path="/ws/matrix_script_result/subtitles/subtitles.srt",
        audio_path="/ws/matrix_script_result/audio/narration.wav",
        shot_count=5,
        duration_seconds=8.0,
        generation_provider="none",
        scene_strategy="ffmpeg_color_card",
        audio_strategy="silent_fallback",
    )
    return minimal_result_record_to_surface_view(minimal_result_summary_to_record(summary))


def _surface_dict():
    return minimal_result_surface_view_to_dict(_surface_view())


# ---------------------------------------------------------------------------
# acceptance #1-#2: surface view -> block with required fields
# ---------------------------------------------------------------------------


def test_surface_view_to_block_has_required_fields() -> None:
    block = minimal_result_surface_view_to_workbench_block(_surface_view())
    assert block["has_result"] is True
    assert block["line_id"] == "matrix_script"
    assert block["final_video_label"] == "本地最小成片"
    assert block["result_status"] == "generated"
    assert block["final_video_path"] == "/ws/matrix_script_result/final/final.mp4"
    assert block["duration_seconds"] == 8.0
    assert block["shot_count"] == 5
    assert block["storage_scope"] == "local_workspace"
    assert block["official_publish_ready"] is False
    assert "尚未进入正式交付存储" in block["operator_note"]


def test_official_publish_ready_pinned_false_even_if_surface_lies() -> None:
    lying = dict(_surface_dict())
    lying["official_publish_ready"] = True  # malicious / drifted input
    block = block_module._block_from_surface_dict(lying)
    assert block["official_publish_ready"] is False


# ---------------------------------------------------------------------------
# wiring adapter (task config)
# ---------------------------------------------------------------------------


def test_derive_from_task_with_config_surface_returns_result() -> None:
    task = {"task_id": "t", "kind": "matrix_script", "config": {"matrix_script_minimal_result": _surface_dict()}}
    block = derive_matrix_script_minimal_result_workbench_block(task)
    assert block["has_result"] is True
    assert block["final_video_path"].endswith("final.mp4")


def test_derive_from_task_without_config_is_empty() -> None:
    assert derive_matrix_script_minimal_result_workbench_block({"config": {}}) == {"has_result": False}
    assert derive_matrix_script_minimal_result_workbench_block({}) == {"has_result": False}
    assert derive_matrix_script_minimal_result_workbench_block("nope") == {"has_result": False}


def test_derive_swallows_malformed_surface() -> None:
    bad = {"config": {"matrix_script_minimal_result": {"has_result": True, "final_video_path": "served by akool"}}}
    # forbidden token in value -> guard trips internally -> empty block (never breaks workbench)
    assert derive_matrix_script_minimal_result_workbench_block(bad) == {"has_result": False}


# ---------------------------------------------------------------------------
# leakage guards (acceptance #3-#6)
# ---------------------------------------------------------------------------


def test_block_serialized_has_no_provider_or_truth_leak() -> None:
    blob = json.dumps(minimal_result_surface_view_to_workbench_block(_surface_view()), ensure_ascii=False).lower()
    for token in (
        "akool", "provider_url", "temporary_url", "download_url", "vendor",
        "model_id", "credit", "provider_task_id", "artifact_key", "r2_key",
        "publish_url", "publish_status", "http://", "https://",
    ):
        assert token not in blob, f"block leaks '{token}'"


def test_block_has_no_publish_or_storage_truth_keys() -> None:
    block = minimal_result_surface_view_to_workbench_block(_surface_view())
    for forbidden_key in ("publish_url", "publish_status", "final_video_key", "artifact_key", "download_url", "r2_key"):
        assert forbidden_key not in block


def test_guard_rejects_injected_publish_url_key() -> None:
    with pytest.raises(WorkbenchResultBlockError):
        assert_no_workbench_block_forbidden_tokens({"publish_url": "x"})


def test_rejects_non_surface_view() -> None:
    with pytest.raises(WorkbenchResultBlockError):
        minimal_result_surface_view_to_workbench_block({"not": "a view"})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# acceptance #7: no Hot Follow / Digital Anchor / Akool / storage import
# ---------------------------------------------------------------------------


def test_module_has_no_forbidden_imports() -> None:
    src = inspect.getsource(block_module)
    assert "providers.akool" not in src
    assert "workers.adapters" not in src
    assert "import httpx" not in src
    for token in (
        "import artifact_storage", "artifact_storage import", "upload_artifact(",
        "get_download_url(", "gateway.app.routers", "gateway.app.services.packet",
        "gateway.app.services.hot_follow", "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"module leaks into {token}"


# ---------------------------------------------------------------------------
# deterministic
# ---------------------------------------------------------------------------


def test_conversion_is_deterministic() -> None:
    a = minimal_result_surface_view_to_workbench_block(_surface_view())
    b = minimal_result_surface_view_to_workbench_block(_surface_view())
    assert a == b


# ---------------------------------------------------------------------------
# template integration (static text) — block present, gated, leak-free
# ---------------------------------------------------------------------------


def test_workbench_template_has_minimal_result_block() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    assert "{% set ms_minimal_result = ((ops.workbench or {}).matrix_script_minimal_result or {}) %}" in src
    assert 'data-role="matrix-script-minimal-result"' in src
    assert "{% if ms_minimal_result.has_result %}" in src


def test_workbench_minimal_result_block_is_read_only_and_leak_free() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    anchor = src.find('data-role="matrix-script-minimal-result"')
    assert anchor != -1
    # slice the exact {% if ms_minimal_result.has_result %} ... {% endif %} block
    gate = src.rfind("{% if ms_minimal_result.has_result %}", 0, anchor)
    assert gate != -1
    end = src.find("{% endif %}", anchor)
    assert end != -1
    block = src[gate : end + len("{% endif %}")]
    # read-only: no media player tag, no external link, no generation control
    for tag in ("<video", "<iframe", "<source ", "<a ", "<button", "<select", "<input"):
        assert tag not in block, f"minimal-result block contains forbidden tag {tag}"
    for token in ("akool", "provider", "vendor", "publish_url", "publish_status", ".mp4", "http://", "https://"):
        assert token not in block.lower(), f"minimal-result block leaks '{token}'"

"""Matrix Script minimal result surface view tests (Phase 3 PR-8R).

Pure unit tests (no ffmpeg). Build a record fixture → operator projection →
surface view, asserting the read-only result surface and all hard boundaries.
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script import minimal_result_surface as surface_module
from gateway.app.services.matrix_script.minimal_result_projection import (
    minimal_result_record_to_operator_projection,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    MatrixScriptMinimalResultRecord,
    minimal_result_summary_to_record,
)
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultSummary,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    MatrixScriptMinimalResultSurfaceView,
    ResultSurfaceError,
    assert_no_result_surface_forbidden_tokens,
    minimal_result_record_to_surface_view,
    minimal_result_surface_view_to_dict,
    operator_projection_to_surface_view,
)


def _record(**overrides):
    summary = MatrixScriptMinimalResultSummary(
        task_id=overrides.pop("task_id", "ms-demo-1"),
        final_video_path=overrides.pop("final_video_path", "/ws/matrix_script_result/final/final.mp4"),
        manifest_path=overrides.pop("manifest_path", "/ws/matrix_script_result/manifest.json"),
        subtitles_path=overrides.pop("subtitles_path", "/ws/matrix_script_result/subtitles/subtitles.srt"),
        audio_path=overrides.pop("audio_path", "/ws/matrix_script_result/audio/narration.wav"),
        shot_count=overrides.pop("shot_count", 5),
        duration_seconds=overrides.pop("duration_seconds", 8.0),
        generation_provider=overrides.pop("generation_provider", "none"),
        scene_strategy=overrides.pop("scene_strategy", "ffmpeg_color_card"),
        audio_strategy=overrides.pop("audio_strategy", "silent_fallback"),
    )
    return minimal_result_summary_to_record(summary)


def _view(**overrides):
    return minimal_result_record_to_surface_view(_record(**overrides))


# ---------------------------------------------------------------------------
# 1-5. conversion + surface shape
# ---------------------------------------------------------------------------


def test_projection_converts_to_surface_view() -> None:
    projection = minimal_result_record_to_operator_projection(_record())
    view = operator_projection_to_surface_view(projection)
    assert isinstance(view, MatrixScriptMinimalResultSurfaceView)
    assert view.line_id == "matrix_script"


def test_surface_has_result_true() -> None:
    assert _view().has_result is True


def test_surface_includes_final_video_local_path() -> None:
    view = _view()
    assert view.final_video_path == "/ws/matrix_script_result/final/final.mp4"
    assert view.final_video_label == "本地最小成片"


def test_surface_storage_scope_is_local_workspace() -> None:
    assert _view().storage_scope == "local_workspace"


def test_surface_official_publish_ready_is_false() -> None:
    assert _view().official_publish_ready is False


def test_surface_operator_note_present_and_result_status_generated() -> None:
    view = _view()
    assert view.result_status == "generated"
    assert "尚未进入正式交付存储" in view.operator_note


# ---------------------------------------------------------------------------
# 6-8. leakage guards
# ---------------------------------------------------------------------------


def test_surface_has_no_publish_fields() -> None:
    d = minimal_result_surface_view_to_dict(_view())
    for forbidden_key in ("publish_url", "publish_status", "official_publish_ready_at"):
        assert forbidden_key not in d
    # official_publish_ready exists but must be False
    assert d["official_publish_ready"] is False


def test_surface_serialized_has_no_provider_or_truth_leak() -> None:
    blob = json.dumps(minimal_result_surface_view_to_dict(_view()), ensure_ascii=False).lower()
    for token in (
        "akool",
        "provider_url",
        "temporary_url",
        "download_url",
        "vendor",
        "model_id",
        "credit",
        "provider_task_id",
        "artifact_key",
        "r2_key",
        "http://",
        "https://",
    ):
        assert token not in blob, f"surface leaks '{token}'"


def test_surface_has_no_storage_truth_keys() -> None:
    d = minimal_result_surface_view_to_dict(_view())
    for forbidden_key in ("final_video_key", "artifact_key", "download_url", "r2_key"):
        assert forbidden_key not in d


def test_guard_rejects_injected_publish_status_key() -> None:
    with pytest.raises(ResultSurfaceError):
        assert_no_result_surface_forbidden_tokens({"publish_status": "live"})


# ---------------------------------------------------------------------------
# 9. no Hot Follow / Digital Anchor / Akool / storage import
# ---------------------------------------------------------------------------


def test_module_has_no_forbidden_imports() -> None:
    src = inspect.getsource(surface_module)
    assert "providers.akool" not in src
    assert "workers.adapters" not in src
    assert "import httpx" not in src
    assert "from swiftcraft" not in src
    assert "import swiftcraft" not in src
    for token in (
        "import artifact_storage",
        "artifact_storage import",
        "upload_artifact(",
        "get_download_url(",
        "gateway.app.routers",
        "gateway.app.templates",
        "gateway.app.services.packet",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"module leaks into {token}"


# ---------------------------------------------------------------------------
# 10. deterministic conversion + validation
# ---------------------------------------------------------------------------


def test_conversion_is_deterministic() -> None:
    a = minimal_result_surface_view_to_dict(_view())
    b = minimal_result_surface_view_to_dict(_view())
    assert a == b


def test_rejects_non_projection_input() -> None:
    with pytest.raises(ResultSurfaceError):
        operator_projection_to_surface_view({"not": "a projection"})  # type: ignore[arg-type]

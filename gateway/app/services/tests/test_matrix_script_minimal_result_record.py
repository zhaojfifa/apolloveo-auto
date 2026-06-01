"""Matrix Script minimal result record tests (Phase 3 PR-6R).

Pure unit tests over ``minimal_result_record.py`` — a summary fixture is built
directly (no ffmpeg). Covers conversion, fixed field values,
publish_ready_candidate logic, serialization, leakage guards, and determinism.
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script import minimal_result_record as record_module
from gateway.app.services.matrix_script.minimal_result_record import (
    GENERATION_PROVIDER_NONE,
    LINE_ID,
    RESULT_STATUS_GENERATED,
    STORAGE_SCOPE_LOCAL,
    MatrixScriptMinimalResultRecord,
    ResultRecordError,
    assert_no_result_record_forbidden_tokens,
    minimal_result_record_to_dict,
    minimal_result_summary_to_record,
)
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultSummary,
)


def _summary(**overrides):
    base = dict(
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
    base.update(overrides)
    return MatrixScriptMinimalResultSummary(**base)


# ---------------------------------------------------------------------------
# 1-4. conversion + fixed field values
# ---------------------------------------------------------------------------


def test_converts_summary_to_record() -> None:
    rec = minimal_result_summary_to_record(_summary())
    assert isinstance(rec, MatrixScriptMinimalResultRecord)
    assert rec.task_id == "ms-demo-1"
    assert rec.shot_count == 5
    assert rec.duration_seconds == 8.0
    assert rec.scene_strategy == "ffmpeg_color_card"
    assert rec.audio_strategy == "silent_fallback"


def test_line_id_is_matrix_script() -> None:
    assert minimal_result_summary_to_record(_summary()).line_id == LINE_ID == "matrix_script"


def test_result_status_is_generated() -> None:
    assert minimal_result_summary_to_record(_summary()).result_status == RESULT_STATUS_GENERATED == "generated"


def test_storage_scope_is_local_workspace() -> None:
    rec = minimal_result_summary_to_record(_summary())
    assert rec.storage_scope == STORAGE_SCOPE_LOCAL == "local_workspace"
    assert rec.generation_provider == GENERATION_PROVIDER_NONE == "none"


# ---------------------------------------------------------------------------
# 5-6. publish_ready_candidate logic
# ---------------------------------------------------------------------------


def test_publish_ready_candidate_true_for_complete_local_result() -> None:
    assert minimal_result_summary_to_record(_summary()).publish_ready_candidate is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"duration_seconds": 0.0},
        {"duration_seconds": -1.0},
        {"shot_count": 0},
        {"final_video_path": ""},
        {"manifest_path": ""},
        {"subtitles_path": ""},
        {"audio_path": ""},
    ],
)
def test_publish_ready_candidate_false_when_incomplete(overrides) -> None:
    rec = minimal_result_summary_to_record(_summary(**overrides))
    assert rec.publish_ready_candidate is False


# ---------------------------------------------------------------------------
# 7. serialization contains expected local paths
# ---------------------------------------------------------------------------


def test_serialized_record_contains_expected_paths() -> None:
    d = minimal_result_record_to_dict(minimal_result_summary_to_record(_summary()))
    assert d["final_video_path"] == "/ws/matrix_script_result/final/final.mp4"
    assert d["manifest_path"] == "/ws/matrix_script_result/manifest.json"
    assert d["subtitles_path"].endswith("subtitles.srt")
    assert d["audio_path"].endswith("narration.wav")
    assert d["line_id"] == "matrix_script"
    assert d["result_status"] == "generated"


# ---------------------------------------------------------------------------
# 8-10. leakage guards
# ---------------------------------------------------------------------------


def test_no_provider_vendor_or_truth_leakage_in_serialized_record() -> None:
    blob = json.dumps(
        minimal_result_record_to_dict(minimal_result_summary_to_record(_summary())), ensure_ascii=False
    ).lower()
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
        assert token not in blob, f"record leaks '{token}'"


def test_serialized_record_has_no_storage_or_publish_keys() -> None:
    d = minimal_result_record_to_dict(minimal_result_summary_to_record(_summary()))
    for forbidden_key in (
        "final_video_key",
        "artifact_key",
        "download_url",
        "r2_key",
        "publish_url",
        "publish_status",
    ):
        assert forbidden_key not in d


def test_guard_rejects_injected_publish_url_key() -> None:
    with pytest.raises(ResultRecordError):
        assert_no_result_record_forbidden_tokens({"publish_url": "x"})


def test_guard_rejects_injected_provider_token_value() -> None:
    with pytest.raises(ResultRecordError):
        assert_no_result_record_forbidden_tokens({"note": "served by akool"})


# ---------------------------------------------------------------------------
# 11. no Akool / provider / adapter / storage dependency
# ---------------------------------------------------------------------------


def test_module_has_no_akool_provider_or_storage_dependency() -> None:
    src = inspect.getsource(record_module)
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
        "gateway.app.services.packet",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"module leaks into {token}"


# ---------------------------------------------------------------------------
# 12. deterministic conversion
# ---------------------------------------------------------------------------


def test_conversion_is_deterministic() -> None:
    a = minimal_result_record_to_dict(minimal_result_summary_to_record(_summary()))
    b = minimal_result_record_to_dict(minimal_result_summary_to_record(_summary()))
    assert a == b


def test_conversion_rejects_non_summary() -> None:
    with pytest.raises(ResultRecordError):
        minimal_result_summary_to_record({"not": "a summary"})  # type: ignore[arg-type]

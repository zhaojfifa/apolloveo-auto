"""Matrix Script minimal result projection tests (Phase 3 PR-7R)."""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script import minimal_result_projection as projection_module
from gateway.app.services.matrix_script.minimal_result_projection import (
    MatrixScriptDeliveryResultProjection,
    MatrixScriptOperatorResultProjection,
    ResultProjectionError,
    assert_no_result_projection_forbidden_tokens,
    delivery_projection_to_dict,
    minimal_result_record_to_delivery_projection,
    minimal_result_record_to_operator_projection,
    operator_projection_to_dict,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    LINE_ID,
    RESULT_STATUS_GENERATED,
    STORAGE_SCOPE_LOCAL,
    MatrixScriptMinimalResultRecord,
)


def _record(**overrides):
    base = dict(
        task_id="ms-demo-1",
        line_id=LINE_ID,
        final_video_path="/ws/matrix_script_result/final/final.mp4",
        manifest_path="/ws/matrix_script_result/manifest.json",
        subtitles_path="/ws/matrix_script_result/subtitles/subtitles.srt",
        audio_path="/ws/matrix_script_result/audio/narration.wav",
        shot_count=5,
        duration_seconds=8.0,
        result_status=RESULT_STATUS_GENERATED,
        publish_ready_candidate=True,
        storage_scope=STORAGE_SCOPE_LOCAL,
        generation_provider="none",
        scene_strategy="ffmpeg_color_card",
        audio_strategy="silent_fallback",
    )
    base.update(overrides)
    return MatrixScriptMinimalResultRecord(**base)


def test_record_to_operator_projection() -> None:
    projection = minimal_result_record_to_operator_projection(_record())
    assert isinstance(projection, MatrixScriptOperatorResultProjection)
    assert projection.task_id == "ms-demo-1"
    assert projection.line_id == "matrix_script"
    assert projection.result_status == "generated"
    assert projection.operator_summary.startswith("operator:")


def test_record_to_delivery_projection() -> None:
    projection = minimal_result_record_to_delivery_projection(_record())
    assert isinstance(projection, MatrixScriptDeliveryResultProjection)
    assert projection.task_id == "ms-demo-1"
    assert projection.line_id == "matrix_script"
    assert projection.result_status == "generated"
    assert projection.delivery_summary.startswith("delivery:")


def test_has_final_video_true_when_final_video_path_is_present() -> None:
    assert minimal_result_record_to_operator_projection(_record()).has_final_video is True
    assert minimal_result_record_to_delivery_projection(_record()).has_final_video is True


def test_has_final_video_false_when_path_is_blank() -> None:
    assert minimal_result_record_to_operator_projection(
        _record(final_video_path="")
    ).has_final_video is False


def test_official_publish_ready_remains_false() -> None:
    op = minimal_result_record_to_operator_projection(_record())
    delivery = minimal_result_record_to_delivery_projection(_record())
    assert op.official_publish_ready is False
    assert delivery.official_publish_ready is False
    assert operator_projection_to_dict(op)["official_publish_ready"] is False
    assert delivery_projection_to_dict(delivery)["official_publish_ready"] is False


def test_publish_ready_candidate_is_candidate_only() -> None:
    op = minimal_result_record_to_operator_projection(_record(publish_ready_candidate=True))
    delivery = minimal_result_record_to_delivery_projection(
        _record(publish_ready_candidate=False)
    )
    assert op.publish_ready_candidate is True
    assert op.official_publish_ready is False
    assert delivery.publish_ready_candidate is False
    assert delivery.official_publish_ready is False


def test_local_paths_are_preserved_as_local_workspace_paths() -> None:
    op = operator_projection_to_dict(minimal_result_record_to_operator_projection(_record()))
    delivery = delivery_projection_to_dict(
        minimal_result_record_to_delivery_projection(_record())
    )
    for payload in (op, delivery):
        assert payload["storage_scope"] == "local_workspace"
        assert payload["final_video_path"] == "/ws/matrix_script_result/final/final.mp4"
        assert payload["manifest_path"] == "/ws/matrix_script_result/manifest.json"
        assert str(payload["subtitles_path"]).endswith("subtitles.srt")
        assert str(payload["audio_path"]).endswith("narration.wav")


def test_forbidden_provider_artifact_publish_fields_are_absent() -> None:
    payloads = (
        operator_projection_to_dict(minimal_result_record_to_operator_projection(_record())),
        delivery_projection_to_dict(minimal_result_record_to_delivery_projection(_record())),
    )
    for payload in payloads:
        for key in (
            "provider_url",
            "temporary_url",
            "download_url",
            "artifact_key",
            "r2_key",
            "publish_url",
            "publish_status",
            "provider_task_id",
            "generation_provider",
        ):
            assert key not in payload


def test_no_akool_vendor_model_credit_leakage() -> None:
    blob = json.dumps(
        {
            "operator": operator_projection_to_dict(
                minimal_result_record_to_operator_projection(_record())
            ),
            "delivery": delivery_projection_to_dict(
                minimal_result_record_to_delivery_projection(_record())
            ),
        },
        ensure_ascii=False,
    ).lower()
    for token in ("akool", "vendor", "model_id", "credit", "provider_task_id"):
        assert token not in blob


def test_guard_rejects_forbidden_field_and_value() -> None:
    with pytest.raises(ResultProjectionError):
        assert_no_result_projection_forbidden_tokens({"publish_url": "x"})
    with pytest.raises(ResultProjectionError):
        assert_no_result_projection_forbidden_tokens({"note": "served by akool"})


def test_deterministic_conversion() -> None:
    a = operator_projection_to_dict(minimal_result_record_to_operator_projection(_record()))
    b = operator_projection_to_dict(minimal_result_record_to_operator_projection(_record()))
    c = delivery_projection_to_dict(minimal_result_record_to_delivery_projection(_record()))
    d = delivery_projection_to_dict(minimal_result_record_to_delivery_projection(_record()))
    assert a == b
    assert c == d


def test_rejects_non_record_and_non_local_scope() -> None:
    with pytest.raises(ResultProjectionError):
        minimal_result_record_to_operator_projection({"not": "a record"})  # type: ignore[arg-type]
    with pytest.raises(ResultProjectionError):
        minimal_result_record_to_delivery_projection(_record(storage_scope="r2"))


def test_no_ui_template_router_or_runtime_import() -> None:
    src = inspect.getsource(projection_module)
    for token in (
        "gateway.app.routers",
        "gateway.app.templates",
        "import artifact_storage",
        "artifact_storage import",
        "upload_artifact(",
        "get_download_url(",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
        "gateway.app.services.packet",
        "providers.akool",
        "workers.adapters",
        "import httpx",
        "import requests",
        "os.environ",
        "os.getenv",
    ):
        assert token not in src, f"projection module leaks into {token}"

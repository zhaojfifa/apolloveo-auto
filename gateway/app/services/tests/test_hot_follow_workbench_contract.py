from __future__ import annotations

import pytest
from pydantic import ValidationError

from gateway.app.services.contracts.hot_follow_workbench import (
    HotFollowWorkbenchResponse,
    validate_hot_follow_workbench_response,
)


def _minimal_payload() -> dict:
    return {
        "task_id": "hf-contract",
        "kind": "hot_follow",
        "line": {"line_id": "hot_follow_line"},
        "pipeline": [
            {"key": "parse", "status": "done", "state": "done"},
            {"key": "subtitles", "status": "done", "state": "done"},
            {"key": "dub", "status": "done", "state": "done"},
            {"key": "compose", "status": "done", "state": "done"},
        ],
        "subtitles": {"subtitle_ready": True, "primary_editable_text": "target"},
        "audio": {"audio_ready": True, "dub_current": True},
        "compose": {"last": {"status": "done"}},
        "deliverables": [{"kind": "final", "status": "done", "state": "done"}],
        "artifact_facts": {
            "subtitle_exists": True,
            "audio_exists": True,
            "final_exists": True,
            "compose_input": {"ready": True},
            "audio_lane": {"mode": "tts_replace_route"},
        },
        "current_attempt": {
            "dub_current": True,
            "audio_ready": True,
            "compose_status": "done",
            "requires_redub": False,
            "requires_recompose": False,
        },
        "ready_gate": {
            "subtitle_ready": True,
            "audio_ready": True,
            "compose_ready": True,
            "publish_ready": True,
            "blocking": [],
        },
        "operator_summary": {"recommended_next_action": "publish"},
        "presentation": {"current_attempt": {"status": "ready"}},
    }


def test_hot_follow_workbench_contract_validates_current_wire_shape_without_rewriting():
    payload = _minimal_payload()

    assert validate_hot_follow_workbench_response(payload) is payload
    model = HotFollowWorkbenchResponse.model_validate(payload)

    assert model.pipeline[0].key == "parse"
    assert model.artifact_facts.final_exists is True
    assert model.current_attempt.dub_current is True
    assert model.ready_gate.publish_ready is True


def test_hot_follow_workbench_contract_requires_four_layer_sections():
    payload = _minimal_payload()
    payload.pop("artifact_facts")

    with pytest.raises(ValidationError):
        HotFollowWorkbenchResponse.model_validate(payload)

from __future__ import annotations

import json
from pathlib import Path

import yaml

from gateway.app.lines.base import LineRegistry
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.status_policy.registry import get_status_runtime_binding


REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_yaml(path: str) -> dict:
    return yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8")) or {}


def _load_json(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def test_veobase01_line_contract_schema_covers_hot_follow_runtime_refs():
    schema = _load_json("docs/contracts/line_contract.schema.json")
    yaml_contract = _load_yaml("docs/architecture/line_contracts/hot_follow_line.yaml")
    line = LineRegistry.for_kind("hot_follow")
    assert line is not None

    required = set(schema["required"])
    assert required <= set(yaml_contract)

    runtime_payload = line.contract_metadata()
    for field in required:
        assert runtime_payload[field] == yaml_contract[field]

    assert runtime_payload["confirmation_policy"] == yaml_contract["confirmation_policy"]
    assert runtime_payload["deliverable_kinds"] == ["final_video", "subtitle", "audio", "pack"]
    assert yaml_contract["deliverables"]["primary"]["kind"] == "final_video"


def test_veobase01_status_runtime_binding_consumes_line_contract_refs():
    binding = get_status_runtime_binding({"kind": "hot_follow"})

    assert binding.kind == "hot_follow"
    assert binding.line is not None
    assert binding.line.line_id == "hot_follow_line"
    assert binding.line.ready_gate_ref == "docs/contracts/hot_follow_ready_gate.yaml"
    assert binding.line.status_policy_ref == "gateway/app/services/status_policy/hot_follow_state.py"
    assert binding.ready_gate_spec is not None
    assert binding.ready_gate_spec.line_id == binding.line.line_id


def test_veobase01_line_runtime_payload_matches_workbench_contract_refs():
    payload = get_line_runtime_binding({"kind": "hot_follow"}).to_payload()

    assert payload["bound"] is True
    assert payload["line_id"] == "hot_follow_line"
    assert payload["hook_refs"] == {
        "skills_bundle_ref": "skills/hot_follow",
        "worker_profile_ref": "docs/contracts/worker_gateway_runtime_contract.md",
        "ready_gate_ref": "docs/contracts/hot_follow_ready_gate.yaml",
        "status_policy_ref": "gateway/app/services/status_policy/hot_follow_state.py",
    }
    assert payload["confirmation_policy"]["before_publish"] is True
    runtime_refs = payload["runtime_refs"]
    assert runtime_refs["line_registry"]["consumed"] is True
    assert runtime_refs["skills_bundle"]["ref"] == payload["skills_bundle_ref"]
    assert runtime_refs["skills_bundle"]["consumed"] is True
    assert runtime_refs["skills_bundle"]["details"]["bundle_id"] == "hot_follow_skills_v1"
    assert runtime_refs["worker_profile"]["ref"] == payload["worker_profile_ref"]
    assert runtime_refs["worker_profile"]["consumed"] is True
    assert runtime_refs["deliverable_profile"]["ref"] == payload["deliverable_profile_ref"]
    assert runtime_refs["deliverable_profile"]["consumed"] is True
    assert runtime_refs["deliverable_profile"]["details"]["primary_kind"] == "final_video"
    assert runtime_refs["asset_sink_profile"]["ref"] == payload["asset_sink_profile_ref"]
    assert runtime_refs["asset_sink_profile"]["consumed"] is True

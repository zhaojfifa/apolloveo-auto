"""Wiring tests for the Digital Anchor publish-hub PR-3 attach seam (OWC-DA PR-3).

Authority:
- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W8 + DA-W9
- mirrors ``test_matrix_script_publish_hub_pr3_attach.py`` discipline

Scope: the seam reads only payload-side keys already attached upstream
by ``publish_hub_payload`` (``digital_anchor_delivery_binding`` +
``digital_anchor_publish_feedback_closure``) and writes the two PR-3
keys (``digital_anchor_delivery_pack`` +
``digital_anchor_delivery_backfill``). Cross-line tasks bypass the
seam (defense-in-depth) so non-Digital-Anchor payloads remain
bytewise unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.digital_anchor import closure_binding
from gateway.app.services.digital_anchor.delivery_binding import (
    project_delivery_binding,
)
from gateway.app.services.digital_anchor.publish_hub_pr3_attach import (
    attach_digital_anchor_delivery_pr3_extras,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "digital_anchor"
    / "sample"
    / "digital_anchor_packet_v1.sample.json"
)


def _packet_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _digital_anchor_task(task_id: str = "da_pr3_attach_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "config": {
            "entry": {
                "topic": "Anchor Launch",
                "language_scope": {
                    "source_language": "en-US",
                    "target_language": ["en-US", "zh-CN"],
                },
                "scene_binding_hint": "scene_template_anchor_a",
            }
        },
        "packet": _packet_sample(),
    }


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def test_seam_attaches_both_keys_for_digital_anchor_task():
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert "digital_anchor_delivery_pack" in payload
    assert "digital_anchor_delivery_backfill" in payload
    pack = payload["digital_anchor_delivery_pack"]
    backfill = payload["digital_anchor_delivery_backfill"]
    assert pack["is_digital_anchor"] is True
    assert backfill["is_digital_anchor"] is True


def test_seam_emits_empty_keys_for_non_digital_anchor_task():
    task = {"task_id": "ms_x", "kind": "matrix_script"}
    payload: Dict[str, Any] = {}
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"] == {}
    assert payload["digital_anchor_delivery_backfill"] == {}


def test_seam_emits_empty_keys_for_hot_follow_task():
    task = {"task_id": "hf_x", "kind": "hot_follow"}
    payload: Dict[str, Any] = {}
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"] == {}
    assert payload["digital_anchor_delivery_backfill"] == {}


def test_seam_emits_empty_keys_for_baseline_task_kind_missing():
    task: Dict[str, Any] = {"task_id": "bl_x"}
    payload: Dict[str, Any] = {}
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"] == {}
    assert payload["digital_anchor_delivery_backfill"] == {}


def test_seam_attaches_when_kind_in_category_key_only():
    """``category_key`` may carry the line id even when ``kind`` doesn't."""
    task = {
        "task_id": "da_x",
        "category_key": "digital_anchor",
        "config": {"entry": {}},
        "packet": _packet_sample(),
    }
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"]["is_digital_anchor"] is True


def test_seam_renders_zero_lane_backfill_when_closure_missing():
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    backfill = payload["digital_anchor_delivery_backfill"]
    assert backfill["is_digital_anchor"] is True
    assert backfill["lane_count"] == 0
    assert backfill["lanes"] == []


def test_seam_renders_real_lanes_when_closure_carries_d1_events():
    task = _digital_anchor_task()
    role_id = task["packet"]["line_specific_refs"][0]["delta"]["roles"][0]["role_id"]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": closure,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    backfill = payload["digital_anchor_delivery_backfill"]
    assert backfill["lane_count"] == 1
    assert backfill["lanes"][0]["row_id"] == role_id


def test_seam_does_not_overwrite_other_payload_keys():
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        "task_id": task["task_id"],
        "media": {"final_video_url": None},
        "operator_surfaces": {"some_key": "preserved"},
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["task_id"] == task["task_id"]
    assert payload["media"] == {"final_video_url": None}
    assert payload["operator_surfaces"] == {"some_key": "preserved"}


def test_seam_defense_in_depth_when_helper_raises(monkeypatch):
    """A helper exception must default both keys to ``{}`` rather than
    crashing the publish hub."""
    import gateway.app.services.digital_anchor.publish_hub_pr3_attach as mod

    def _raise(*_args, **_kwargs):
        raise RuntimeError("simulated projection error")

    # Patch the import-time helper resolution by monkey-patching the
    # attribute *inside* the module namespace AFTER the import call. The
    # seam imports lazily inside the try block, so we patch the source
    # module to make the underlying derive function raise.
    from gateway.app.services.digital_anchor import delivery_pack_view

    monkeypatch.setattr(
        delivery_pack_view, "derive_digital_anchor_delivery_pack", _raise
    )
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    mod.attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"] == {}
    assert payload["digital_anchor_delivery_backfill"] == {}


def test_seam_module_does_not_import_gateway_app_config():
    """Wiring tests must load on Python 3.9 without the PEP-604 baseline
    issue. The seam module must not import ``gateway.app.config`` at
    module load (mirror of MS PR-3 attach seam discipline)."""
    import importlib

    mod = importlib.import_module(
        "gateway.app.services.digital_anchor.publish_hub_pr3_attach"
    )
    # The module's globals must not carry a `config` attribute pulled
    # from gateway.app at import time.
    assert "config" not in vars(mod)


def test_seam_attaches_both_keys_idempotently():
    """Calling the seam twice on the same payload yields stable output."""
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        "digital_anchor_delivery_binding": project_delivery_binding(task["packet"]),
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    first_pack = payload["digital_anchor_delivery_pack"]
    first_backfill = payload["digital_anchor_delivery_backfill"]
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    assert payload["digital_anchor_delivery_pack"] == first_pack
    assert payload["digital_anchor_delivery_backfill"] == first_backfill


def test_seam_handles_task_without_packet_view():
    """If upstream did not attach digital_anchor_delivery_binding, the
    seam still calls derive_digital_anchor_delivery_pack with ``{}``,
    which returns ``{}`` (not is_digital_anchor)."""
    task = _digital_anchor_task()
    payload: Dict[str, Any] = {
        # No digital_anchor_delivery_binding key.
        "digital_anchor_publish_feedback_closure": None,
    }
    attach_digital_anchor_delivery_pr3_extras(payload=payload, task=task)
    # delivery_pack returns {} because the projection input is empty
    assert payload["digital_anchor_delivery_pack"] == {}
    # backfill returns the digital-anchor-shaped empty bundle
    assert payload["digital_anchor_delivery_backfill"]["is_digital_anchor"] is True
    assert payload["digital_anchor_delivery_backfill"]["lane_count"] == 0

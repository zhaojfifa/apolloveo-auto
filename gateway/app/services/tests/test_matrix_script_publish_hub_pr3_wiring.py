"""OWC-MS PR-3 — Delivery Center copy_bundle + 多渠道回填 wiring tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W7 + MS-W8 (binding scope).
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §4 (forbidden — no Hot Follow /
  Digital Anchor file touch; no second producer; no schema widening).
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §5.1 (per-PR file isolation).
- ``ENGINEERING_RULES.md`` §13 Product-Flow Module Presence.
- Wiring seam: ``gateway/app/services/task_view_helpers.py::publish_hub_payload``.

Import-light: drives ``publish_hub_payload`` directly with hand-built
matrix_script / hot_follow / digital_anchor / baseline tasks. Confirms
the two new bundle keys (``matrix_script_delivery_copy_bundle`` /
``matrix_script_delivery_backfill``) attach inside the matrix_script
branch only and that closure write-back state flows into the 回填 lanes.

What is proved:

1. matrix_script task: payload carries
   ``matrix_script_delivery_copy_bundle.is_matrix_script == True`` +
   ``matrix_script_delivery_backfill.is_matrix_script == True``.
2. matrix_script with no closure yet: 回填 has zero lanes (closure
   lazy-creation never happens on read; Recovery PR-3 invariant).
3. matrix_script with operator_publish event: 回填 carries the lane
   for that variation_id with publish_url + publish_status resolved.
4. Hot Follow task: payload carries NEITHER PR-3 key (cross-line
   isolation).
5. Digital Anchor task: payload carries NEITHER PR-3 key (cross-line
   isolation).
6. Baseline / unknown kind: payload carries NEITHER PR-3 key.
7. The 回填 helper consumes the same closure view the existing PR-3
   ``matrix_script_publish_feedback_closure`` block consumes — single
   truth source.
8. No vendor / model / provider / engine identifier flows through the
   wiring (recursive walk).
9. The PR-2 / PR-U3 keys (``matrix_script_delivery_comprehension`` /
   ``matrix_script_publish_feedback_closure``) remain attached for
   matrix_script tasks (no regression).
10. The seam consumes the existing publish-hub ``copy_bundle`` so the
    Hot Follow-flavored caption surfaces as the Matrix Script title
    without re-implementing caption derivation.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

# `publish_hub_payload` transitively imports `gateway.app.config`, which uses
# PEP-604 `str | None` syntax (Python 3.10+). On Python 3.9 this raises a
# TypeError at import time. The same pre-existing repo baseline limitation is
# documented in OWC-MS PR-2 / OWC-MS PR-1 / Recovery PR-1..PR-4 execution logs.
# CI on Python 3.10+ exercises the full set; skip on 3.9 to keep the import-
# light suite green while preserving coverage on supported interpreters.
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="publish_hub_payload imports gateway.app.config which uses PEP-604 unions (Python 3.10+).",
)

from gateway.app.services.matrix_script import closure_binding


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "matrix_script"
    / "sample"
    / "matrix_script_packet_v1.sample.json"
)


def _packet_sample() -> dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _matrix_script_task() -> dict[str, Any]:
    packet = _packet_sample()
    return {
        "task_id": "ms_pr3_wiring_001",
        "id": "ms_pr3_wiring_001",
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "title": "PR-3 wiring task",
        "ready_gate": {"publishable": True, "blocking": []},
        "packet": packet,
        "line_specific_refs": packet["line_specific_refs"],
        "line_id": "matrix_script",
        "binding": packet.get("binding") or {},
        "config": {
            "line_id": "matrix_script",
            "entry": {
                "topic": "国货高端面霜矩阵",
                "target_platform": "douyin",
                "audience_hint": "26-35 都市女性",
                "tone_hint": "理性 · 信赖",
                "length_hint": "30-45s",
                "operator_notes": "",
            },
        },
    }


def _hot_follow_task() -> dict[str, Any]:
    return {
        "task_id": "hf_isolation_001",
        "id": "hf_isolation_001",
        "kind": "hot_follow",
        "category_key": "hot_follow",
        "title": "Hot Follow isolation",
    }


def _digital_anchor_task() -> dict[str, Any]:
    return {
        "task_id": "da_isolation_001",
        "id": "da_isolation_001",
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "title": "Digital Anchor isolation",
    }


def _cells(packet: dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    raise AssertionError("variation cells missing from packet sample")


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


# Lazy import via the helper module so the module-level import bundle
# stays light. ``publish_hub_payload`` pulls in artifact_storage; the
# import is local to the test body so import-light scanners don't choke.
def _publish_hub_payload(task: dict[str, Any]):
    from gateway.app.services.task_view_helpers import publish_hub_payload

    return publish_hub_payload(task)


def test_matrix_script_payload_carries_pr3_copy_bundle_and_backfill_keys():
    payload = _publish_hub_payload(_matrix_script_task())
    assert isinstance(payload.get("matrix_script_delivery_copy_bundle"), dict)
    assert payload["matrix_script_delivery_copy_bundle"]["is_matrix_script"] is True
    assert isinstance(payload.get("matrix_script_delivery_backfill"), dict)
    assert payload["matrix_script_delivery_backfill"]["is_matrix_script"] is True


def test_matrix_script_payload_with_no_closure_emits_zero_backfill_lanes():
    payload = _publish_hub_payload(_matrix_script_task())
    backfill = payload["matrix_script_delivery_backfill"]
    assert backfill["lane_count"] == 0
    assert backfill["lanes"] == []


def test_matrix_script_payload_with_published_closure_renders_backfill_lane():
    task = _matrix_script_task()
    cell_ids = _cells(task["packet"])
    target_cell = cell_ids[0]
    closure_binding.get_or_create_for_task(task)
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": target_cell,
            "actor_kind": "operator",
            "recorded_at": "2026-05-05T12:00:00Z",
            "payload": {
                "publish_url": "https://www.douyin.com/video/abc",
                "publish_status": "pending",
            },
        },
    )
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "platform_callback",
            "variation_id": target_cell,
            "actor_kind": "platform",
            "recorded_at": "2026-05-05T13:00:00Z",
            "payload": {
                "publish_status": "published",
                "publish_url": "https://www.douyin.com/video/abc",
            },
        },
    )
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "metrics_snapshot",
            "variation_id": target_cell,
            "actor_kind": "system",
            "recorded_at": "2026-05-05T14:00:00Z",
            "payload": {
                "channel_id": "douyin",
                "captured_at": "2026-05-05T14:00:00Z",
                "impressions": 12345,
                "views": 9000,
            },
        },
    )

    payload = _publish_hub_payload(task)
    backfill = payload["matrix_script_delivery_backfill"]
    lanes_by_id = {lane["variation_id"]: lane for lane in backfill["lanes"]}
    target_lane = lanes_by_id[target_cell]
    field_map = {field["field_id"]: field for field in target_lane["fields"]}

    assert field_map["publish_url"]["value"] == "https://www.douyin.com/video/abc"
    assert field_map["publish_status"]["value"] == "published"
    assert field_map["channel"]["value"] == "douyin"
    metrics = field_map["metrics_snapshot"]
    pairs = {p["metric_id"]: p["value"] for p in metrics["metrics_pairs"]}
    assert pairs["impressions"] == 12345
    assert pairs["views"] == 9000


def test_matrix_script_payload_uses_existing_publish_hub_copy_bundle_for_title():
    """Seam invariant: the MS-W7 helper consumes the publish hub's existing
    ``copy_bundle`` (built by ``_build_copy_bundle``) so the Hot Follow-flavored
    caption — which derives from ``mm.txt`` / task title — surfaces as the
    Matrix Script title without re-implementing caption derivation."""

    task = _matrix_script_task()
    payload = _publish_hub_payload(task)
    base_copy = payload["copy_bundle"]
    title_subfield = next(
        sub
        for sub in payload["matrix_script_delivery_copy_bundle"]["subfields"]
        if sub["subfield_id"] == "title"
    )
    if base_copy.get("caption"):
        # The caption fallback path: title resolves from the publish hub
        # copy_bundle.caption first.
        assert title_subfield["value"] == base_copy["caption"].strip()
        assert title_subfield["value_source_id"] == "delivery_copy_bundle_caption"
    else:
        # No caption available → fall back to entry.topic.
        assert title_subfield["value"] == task["config"]["entry"]["topic"]
        assert title_subfield["value_source_id"] == "matrix_script_entry_topic"


def test_hot_follow_payload_carries_neither_pr3_key():
    payload = _publish_hub_payload(_hot_follow_task())
    assert "matrix_script_delivery_copy_bundle" not in payload
    assert "matrix_script_delivery_backfill" not in payload


def test_digital_anchor_payload_carries_neither_pr3_key():
    payload = _publish_hub_payload(_digital_anchor_task())
    assert "matrix_script_delivery_copy_bundle" not in payload
    assert "matrix_script_delivery_backfill" not in payload


def test_baseline_unknown_kind_payload_carries_neither_pr3_key():
    payload = _publish_hub_payload(
        {"task_id": "baseline_001", "id": "baseline_001", "kind": ""}
    )
    assert "matrix_script_delivery_copy_bundle" not in payload
    assert "matrix_script_delivery_backfill" not in payload


def test_pr2_and_pr_u3_keys_remain_attached_for_matrix_script_tasks():
    payload = _publish_hub_payload(_matrix_script_task())
    # Pre-existing keys MUST continue to attach (no regression).
    assert "matrix_script_delivery_comprehension" in payload
    assert "matrix_script_publish_feedback_closure" in payload
    assert "operator_surfaces" in payload


def test_backfill_helper_reads_same_closure_as_existing_pr3_block():
    """Single-truth invariant: the 回填 helper and the existing PR-3
    ``matrix_script_publish_feedback_closure`` block both read the same
    closure view; they never divergence on the closure_id."""

    task = _matrix_script_task()
    cell_ids = _cells(task["packet"])
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cell_ids[0],
            "actor_kind": "operator",
            "payload": {"publish_url": "https://example.test/u", "publish_status": "pending"},
        },
    )
    payload = _publish_hub_payload(task)
    closure = payload["matrix_script_publish_feedback_closure"]
    backfill = payload["matrix_script_delivery_backfill"]
    closure_variation_ids = {row["variation_id"] for row in closure["variation_feedback"]}
    backfill_variation_ids = {lane["variation_id"] for lane in backfill["lanes"]}
    assert closure_variation_ids == backfill_variation_ids


def _walk_strings(value):
    from typing import Mapping

    if isinstance(value, Mapping):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


@pytest.mark.parametrize("token", ["vendor", "model_id", "provider", "engine"])
def test_pr3_bundle_keys_carry_no_forbidden_token_recursively(token):
    task = _matrix_script_task()
    cell_ids = _cells(task["packet"])
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cell_ids[0],
            "actor_kind": "operator",
            "payload": {"publish_url": "https://example.test/p", "publish_status": "pending"},
        },
    )
    payload = _publish_hub_payload(task)
    for key in ("matrix_script_delivery_copy_bundle", "matrix_script_delivery_backfill"):
        bundle = payload.get(key, {})
        for s in _walk_strings(bundle):
            assert token not in s.lower(), f"token {token!r} leaked into {key}: {s!r}"


def test_seam_does_not_lazy_create_closure_when_none_exists():
    """Read-only closure consumption invariant. ``get_closure_view_for_task``
    must NEVER lazy-create a closure on the publish-hub read path."""

    task = _matrix_script_task()
    # Sanity-check store empty before payload build.
    assert closure_binding.get_closure_view_for_task(task["task_id"]) is None
    _publish_hub_payload(task)
    # Still empty afterwards: the read path did not lazy-create.
    assert closure_binding.get_closure_view_for_task(task["task_id"]) is None


def test_seam_attaches_pr3_keys_alongside_pr_u3_comprehension():
    """Composition invariant: PR-3 keys + PR-U3 comprehension key all attach
    inside the same ``kind == "matrix_script"`` seam without one shadowing
    another."""

    payload = _publish_hub_payload(_matrix_script_task())
    pr_u3 = payload.get("matrix_script_delivery_comprehension", {})
    pr3_copy = payload.get("matrix_script_delivery_copy_bundle", {})
    pr3_backfill = payload.get("matrix_script_delivery_backfill", {})
    assert pr_u3.get("is_matrix_script") is True
    assert pr3_copy.get("is_matrix_script") is True
    assert pr3_backfill.get("is_matrix_script") is True


def test_helper_does_not_mutate_task_config_entry():
    task = _matrix_script_task()
    snapshot = deepcopy(task["config"]["entry"])
    _publish_hub_payload(task)
    assert task["config"]["entry"] == snapshot

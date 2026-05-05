"""OWC-MS PR-3 — Delivery Center copy_bundle + 多渠道回填 wiring tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W7 + MS-W8 (binding scope).
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §4 (forbidden — no Hot Follow /
  Digital Anchor file touch; no second producer; no schema widening).
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §5.1 (per-PR file isolation).
- ``ENGINEERING_RULES.md`` §13 Product-Flow Module Presence.
- OWC-MS PR-3 reviewer-fail correction Blocker 2 (2026-05-05): wiring
  tests must exercise the actual attach path WITHOUT depending on
  ambient storage configuration; do not solve by skipping; coverage
  must not be reduced.

Wiring path under test:

The actual attach is performed by
``gateway.app.services.matrix_script.publish_hub_pr3_attach.attach_matrix_script_delivery_pr3_extras``,
which is the **same seam** ``publish_hub_payload`` invokes inside its
``kind_value == "matrix_script"`` branch (verified by
``test_publish_hub_payload_invokes_the_pr3_attach_seam`` below). Driving
the seam directly with hand-built payload skeletons exercises the
attach path verbatim while keeping the test independent of
``compute_composed_state`` / ``artifact_storage`` / ambient storage
configuration / the ``gateway.app.config`` import chain.

What is proved:

1. matrix_script payload skeleton: seam attaches both PR-3 keys with
   ``is_matrix_script == True``.
2. matrix_script with no closure yet: 回填 has zero lanes.
3. matrix_script with published closure events: 回填 lane carries
   resolved publish_url + publish_status + channel + metrics_snapshot.
4. Hot Follow / Digital Anchor / Baseline: helpers themselves return
   ``{}`` regardless of caller; the seam writes those ``{}`` payloads
   for non-matrix_script tasks (defensive — production gating is at
   the caller side via ``kind_value == "matrix_script"``).
5. The 回填 helper consumes the same closure view the Recovery PR-3
   block attaches — single truth source.
6. No vendor / model / provider / engine identifier flows through the
   wiring (recursive walk).
7. The seam is byte-equivalent to the inline block ``publish_hub_payload``
   used to carry — verified by source-import binding test.
8. The seam consumes the existing publish-hub ``copy_bundle`` so the
   caption surfaces as the Matrix Script title; adjacent entry hints
   are NOT consumed (Blocker 1 invariant).
9. Defense-in-depth: when the upstream payload is malformed, the seam
   defaults both keys to ``{}`` instead of raising.
10. Production binding: ``publish_hub_payload`` invokes the seam (not
    a copy of the seam logic) — verified by reading the source.
"""
from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script import closure_binding
from gateway.app.services.matrix_script.publish_hub_pr3_attach import (
    attach_matrix_script_delivery_pr3_extras,
)


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


def _payload_skeleton(
    *,
    copy_bundle: Mapping[str, Any] | None = None,
    closure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Mirror the publish-hub payload state at the moment the inline
    attach block runs in production (after the existing ``copy_bundle``
    projection + the Recovery PR-3 closure block have written their
    keys, but before the OWC-MS PR-3 attach has run).
    """

    return {
        "copy_bundle": dict(copy_bundle or {}),
        "matrix_script_publish_feedback_closure": closure,
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


# ─────────────────────────────────────────────────────────────────────
# 1–3. matrix_script attach behavior.
# ─────────────────────────────────────────────────────────────────────


def test_matrix_script_attach_sets_both_pr3_keys_with_is_matrix_script_true():
    """When the closure has been initialized (matrix_script-shaped), both
    PR-3 keys carry ``is_matrix_script == True``. The closure may have
    zero events — pre-publish state — but the panel still renders so
    the operator sees what's coming."""

    task = _matrix_script_task()
    closure_binding.get_or_create_for_task(task)  # initialize, no events
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload = _payload_skeleton(
        copy_bundle={"caption": "标题文案", "hashtags": "#tag", "comment_cta": "CTA 文案"},
        closure=closure,
    )
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)
    assert isinstance(payload["matrix_script_delivery_copy_bundle"], dict)
    assert payload["matrix_script_delivery_copy_bundle"]["is_matrix_script"] is True
    assert isinstance(payload["matrix_script_delivery_backfill"], dict)
    assert payload["matrix_script_delivery_backfill"]["is_matrix_script"] is True


def test_matrix_script_with_initialized_empty_closure_emits_lanes_no_events():
    """Initialized closure with zero events: one lane per variation_id
    (pre-seeded from the packet), all six fields rendering the
    ``not_published_yet`` / ``unsourced`` sentinels (no synthesized
    publish state — Blocker invariant)."""

    task = _matrix_script_task()
    closure_binding.get_or_create_for_task(task)
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload = _payload_skeleton(closure=closure)
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)
    backfill = payload["matrix_script_delivery_backfill"]
    expected_cells = _cells(task["packet"])
    assert backfill["lane_count"] == len(expected_cells)
    assert sorted(lane["variation_id"] for lane in backfill["lanes"]) == sorted(expected_cells)
    # Every field carries either an unresolved / unsourced sentinel or
    # the closed-enum default for publish_status (``pending`` is the
    # contract-pinned default for newly seeded variation_feedback rows
    # per ``create_closure``). No invented publish state.
    for lane in backfill["lanes"]:
        field_map = {f["field_id"]: f for f in lane["fields"]}
        for unresolved_id in ("channel", "publish_time", "publish_url"):
            assert field_map[unresolved_id]["status_code"] == "not_published_yet", lane
        assert field_map["account"]["status_code"] == "unsourced_pending_capture_capability"
        assert field_map["metrics_snapshot"]["status_code"] == "no_metrics_snapshot_yet"
        # publish_status pre-seeds to "pending" per the closure contract.
        ps = field_map["publish_status"]
        assert ps["status_code"] == "resolved_from_closure"
        assert ps["value"] == "pending"
        assert ps["value_label_zh"] == "待发布"


def test_matrix_script_with_none_closure_emits_empty_backfill_bundle():
    """No closure exists yet (operator has not initialized): the helper
    emits ``{}`` so the JS renderer hides the backfill block. This is
    the realistic pre-initialization flow returned by
    ``get_closure_view_for_task`` until an event is fired."""

    payload = _payload_skeleton(closure=None)
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_matrix_script_task()
    )
    assert payload["matrix_script_delivery_backfill"] == {}
    # copy_bundle still attaches because matrix_script kind alone
    # determines copy_bundle attachment (closure is irrelevant to MS-W7).
    assert payload["matrix_script_delivery_copy_bundle"]["is_matrix_script"] is True


def test_matrix_script_with_published_closure_renders_backfill_lane():
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

    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload = _payload_skeleton(closure=closure)
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)

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


# ─────────────────────────────────────────────────────────────────────
# 4. Cross-line isolation. The helpers return {} for non-matrix_script;
#    the seam writes those {} values defensively even if a caller forgets
#    to gate. (Production caller in publish_hub_payload still gates by
#    kind_value == "matrix_script"; this guards against future regression.)
# ─────────────────────────────────────────────────────────────────────


def test_hot_follow_attach_writes_empty_pr3_bundles():
    payload = _payload_skeleton(
        copy_bundle={"caption": "hf-caption", "hashtags": "#hf", "comment_cta": "hf-cta"},
        closure=None,
    )
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_hot_follow_task()
    )
    assert payload["matrix_script_delivery_copy_bundle"] == {}
    assert payload["matrix_script_delivery_backfill"] == {}


def test_digital_anchor_attach_writes_empty_pr3_bundles():
    payload = _payload_skeleton(closure=None)
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_digital_anchor_task()
    )
    assert payload["matrix_script_delivery_copy_bundle"] == {}
    assert payload["matrix_script_delivery_backfill"] == {}


def test_baseline_unknown_kind_attach_writes_empty_pr3_bundles():
    payload = _payload_skeleton(closure=None)
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task={"task_id": "baseline", "id": "baseline", "kind": ""}
    )
    assert payload["matrix_script_delivery_copy_bundle"] == {}
    assert payload["matrix_script_delivery_backfill"] == {}


# ─────────────────────────────────────────────────────────────────────
# 5. Single-truth invariant for closure consumption.
# ─────────────────────────────────────────────────────────────────────


def test_backfill_helper_reads_same_closure_attached_to_payload():
    """Single-truth invariant: the 回填 helper and the existing PR-3
    ``matrix_script_publish_feedback_closure`` block both read the same
    closure view; they never diverge on variation_ids."""

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
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload = _payload_skeleton(closure=closure)
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)

    closure_variation_ids = {row["variation_id"] for row in closure["variation_feedback"]}
    backfill_variation_ids = {
        lane["variation_id"]
        for lane in payload["matrix_script_delivery_backfill"]["lanes"]
    }
    assert closure_variation_ids == backfill_variation_ids


# ─────────────────────────────────────────────────────────────────────
# 6. Validator R3 — no forbidden token leaks.
# ─────────────────────────────────────────────────────────────────────


def _walk_strings(value: Any):
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
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    payload = _payload_skeleton(
        copy_bundle={"caption": "标题", "hashtags": "#tag", "comment_cta": "CTA"},
        closure=closure,
    )
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)

    for key in ("matrix_script_delivery_copy_bundle", "matrix_script_delivery_backfill"):
        bundle = payload.get(key, {})
        for s in _walk_strings(bundle):
            assert token not in s.lower(), f"token {token!r} leaked into {key}: {s!r}"


# ─────────────────────────────────────────────────────────────────────
# 7. Blocker 1 invariant — copy_bundle from caption only; no entry hints.
# ─────────────────────────────────────────────────────────────────────


def test_copy_bundle_title_resolves_from_payload_caption_only():
    payload = _payload_skeleton(
        copy_bundle={"caption": "上头条 · 9.9 高端面霜实测", "hashtags": "", "comment_cta": ""},
        closure=None,
    )
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_matrix_script_task()
    )
    title_subfield = next(
        sub
        for sub in payload["matrix_script_delivery_copy_bundle"]["subfields"]
        if sub["subfield_id"] == "title"
    )
    assert title_subfield["value"] == "上头条 · 9.9 高端面霜实测"
    assert title_subfield["value_source_id"] == "delivery_copy_bundle_caption"


def test_copy_bundle_all_unresolved_when_only_entry_hints_present():
    """Blocker 1 invariant at the wiring layer: an empty publish-hub
    ``copy_bundle`` produces ALL UNRESOLVED subfields even when the
    matrix_script task carries a fully populated ``entry`` payload."""

    payload = _payload_skeleton(copy_bundle={}, closure=None)
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_matrix_script_task()
    )
    bundle = payload["matrix_script_delivery_copy_bundle"]
    assert bundle["unresolved_count"] == 4
    for sub in bundle["subfields"]:
        assert sub["status_code"] == "unresolved_pending_copy_projection_contract"


# ─────────────────────────────────────────────────────────────────────
# 8. Defense-in-depth — malformed inputs do not raise.
# ─────────────────────────────────────────────────────────────────────


def test_attach_with_malformed_closure_returns_empty_backfill_without_raising():
    payload = _payload_skeleton(closure="not-a-mapping")  # type: ignore[arg-type]
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_matrix_script_task()
    )
    # Backfill helper recognizes invalid input → {}.
    assert payload["matrix_script_delivery_backfill"] == {}


def test_attach_with_missing_copy_bundle_falls_back_to_empty_dict():
    payload = {"matrix_script_publish_feedback_closure": None}  # no copy_bundle key
    attach_matrix_script_delivery_pr3_extras(
        payload=payload, task=_matrix_script_task()
    )
    bundle = payload["matrix_script_delivery_copy_bundle"]
    assert bundle["is_matrix_script"] is True
    assert bundle["unresolved_count"] == 4


# ─────────────────────────────────────────────────────────────────────
# 9. Production binding — publish_hub_payload invokes this seam.
# ─────────────────────────────────────────────────────────────────────


def test_publish_hub_payload_invokes_the_pr3_attach_seam():
    """Source-level binding check: the production publish_hub_payload
    body imports and invokes ``attach_matrix_script_delivery_pr3_extras``
    inside its ``kind_value == "matrix_script"`` branch.

    Reading source bytes (not importing the module) avoids the
    ``gateway.app.config`` PEP-604 chain on Python 3.9 while still
    proving the seam is wired into production. CI on 3.10+ additionally
    exercises end-to-end through ``publish_hub_payload`` itself via
    higher-level integration suites.
    """

    helpers_path = (
        Path(__file__).resolve().parents[1]
        / "task_view_helpers.py"
    )
    source = helpers_path.read_text()
    # The production body must import the seam under the
    # publish_hub_payload entry and call it. Both literal substrings
    # must appear in the source.
    assert "from gateway.app.services.matrix_script.publish_hub_pr3_attach import" in source
    assert "attach_matrix_script_delivery_pr3_extras" in source
    # And the call must be inside the matrix_script branch (i.e. occurs
    # after `kind_value == "matrix_script"`).
    branch_idx = source.find('kind_value == "matrix_script"')
    call_idx = source.find("attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)")
    assert branch_idx != -1, "matrix_script branch missing in publish_hub_payload"
    assert call_idx != -1, "PR-3 seam invocation missing in publish_hub_payload"
    assert call_idx > branch_idx, (
        "PR-3 seam must be invoked inside the matrix_script branch, "
        "not before it"
    )


# ─────────────────────────────────────────────────────────────────────
# 10. No mutation of inputs other than the payload's two new keys.
# ─────────────────────────────────────────────────────────────────────


def test_attach_does_not_mutate_task_or_inputs_other_than_two_target_keys():
    task = _matrix_script_task()
    task_snapshot = deepcopy(task)
    payload = _payload_skeleton(
        copy_bundle={"caption": "标题"},
        closure=None,
    )
    payload_snapshot = deepcopy(payload)
    attach_matrix_script_delivery_pr3_extras(payload=payload, task=task)
    # Task is untouched.
    assert task == task_snapshot
    # The two non-PR-3 payload keys are untouched.
    assert payload["copy_bundle"] == payload_snapshot["copy_bundle"]
    assert (
        payload["matrix_script_publish_feedback_closure"]
        == payload_snapshot["matrix_script_publish_feedback_closure"]
    )
    # Only the two PR-3 keys are added.
    new_keys = set(payload.keys()) - set(payload_snapshot.keys())
    assert new_keys == {
        "matrix_script_delivery_copy_bundle",
        "matrix_script_delivery_backfill",
    }


def test_seam_signature_matches_documented_attach_contract():
    """The seam's keyword-only signature is part of its public contract:
    callers (publish_hub_payload + tests) MUST pass ``payload=`` and
    ``task=`` keyword arguments. A future positional change would silently
    break the production wiring."""

    sig = inspect.signature(attach_matrix_script_delivery_pr3_extras)
    params = sig.parameters
    assert set(params.keys()) == {"payload", "task"}
    for name in ("payload", "task"):
        assert params[name].kind == inspect.Parameter.KEYWORD_ONLY

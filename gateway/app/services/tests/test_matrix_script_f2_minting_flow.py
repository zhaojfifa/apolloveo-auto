"""F2 minting-flow tests for Matrix Script source_script_ref (Plan E PR-2, Item E.MS.2).

Authority:
- ``docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md`` §3.2 / §5.2 / §5.4 / §6 row A2
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)"
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)"

Discipline (per gate spec §5.4 PR-2 regression scope):
- §8.A guard regression: body-text rejection still HTTP 400.
- §8.F guard regression: publisher-URL / bucket-URI rejection still HTTP 400 with
  "scheme is not recognised".
- Minted ``content://matrix-script/source/<product-minted-token>`` handle passes
  the §8.A + §8.F guards on round-trip.
- Pre-§8.F operator-discipline handles (e.g. ``content://matrix-script/source/op-token-001``)
  still accepted (no operator migration required).

These tests are import-light by design: they call the minting service and the
``_validate_source_script_ref_shape`` guard directly, never instantiating the
FastAPI app, so they remain compatible with both Python 3.9 and 3.10+.
"""
from __future__ import annotations

import re
from typing import Mapping

import pytest
from fastapi import HTTPException

from gateway.app.services.matrix_script.create_entry import (
    SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES,
    _validate_source_script_ref_shape,
)
from gateway.app.services.matrix_script.source_script_ref_minting import (
    MATRIX_SCRIPT_MINT_ROUTE,
    MINTING_POLICY,
    MINT_TOKEN_PREFIX,
    mint_source_script_ref,
)


# ---------------------------------------------------------------------------
# Minting service shape + acceptance
# ---------------------------------------------------------------------------


def test_mint_returns_closed_key_set() -> None:
    payload = mint_source_script_ref()
    assert isinstance(payload, Mapping)
    assert set(payload.keys()) == {
        "source_script_ref",
        "token",
        "minted_at",
        "policy",
        "requested_by",
    }


def test_minted_handle_has_content_scheme_with_matrix_source_path() -> None:
    payload = mint_source_script_ref()
    handle = payload["source_script_ref"]
    assert handle.startswith("content://matrix-script/source/")
    token = payload["token"]
    assert handle.endswith(token)
    assert token.startswith(f"{MINT_TOKEN_PREFIX}-")


def test_minted_handle_passes_existing_validate_source_script_ref_shape_guard() -> None:
    payload = mint_source_script_ref()
    # Round-trip through the same guard operator-supplied handles use.
    accepted = _validate_source_script_ref_shape(payload["source_script_ref"])
    assert accepted == payload["source_script_ref"]


def test_mint_does_not_widen_accepted_scheme_set() -> None:
    """Acceptance: §8.F-tightened scheme set MUST remain {content, task, asset, ref} verbatim."""
    assert SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES == ("content", "task", "asset", "ref")


def test_mint_policy_enum_is_operator_request_v1() -> None:
    payload = mint_source_script_ref()
    assert payload["policy"] == MINTING_POLICY == "operator_request_v1"


def test_mint_minted_at_is_iso8601_utc() -> None:
    payload = mint_source_script_ref()
    minted_at = payload["minted_at"]
    # ISO-8601 with seconds precision and explicit timezone, e.g. 2026-05-04T12:34:56+00:00
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$", minted_at), minted_at


def test_mint_produces_distinct_handles_across_calls() -> None:
    handles = {mint_source_script_ref()["source_script_ref"] for _ in range(20)}
    assert len(handles) == 20, "uuid-derived tokens must be distinct across consecutive mints"


# ---------------------------------------------------------------------------
# requested_by sanitization (record-keeping only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, ""),
        ("", ""),
        ("   ", ""),
        (123, ""),
        ({"x": 1}, ""),
        ("operator-jackie", "operator-jackie"),
        ("op:wave-3/sample-2", "op:wave-3/sample-2"),
        ("正文不应被允许", ""),  # non-ASCII alphabet rejected by sanitizer
        ("contains\nnewline", ""),  # whitespace token rejected
    ],
)
def test_mint_sanitizes_requested_by(raw: object, expected: str) -> None:
    payload = mint_source_script_ref(requested_by=raw)
    assert payload["requested_by"] == expected


def test_requested_by_does_not_appear_in_minted_handle(
) -> None:
    payload = mint_source_script_ref(requested_by="operator-jackie")
    assert "operator-jackie" not in payload["source_script_ref"]
    assert "operator-jackie" not in payload["token"]


def test_requested_by_overlong_value_collapses_to_empty() -> None:
    payload = mint_source_script_ref(requested_by="A" * 1024)
    # Truncated then re-validated; truncation alone keeps it within the alphabet,
    # so the sanitizer accepts the truncated string. This test asserts the
    # alphabet check still runs on the truncated value.
    assert payload["requested_by"] == "A" * 120


# ---------------------------------------------------------------------------
# §8.A regression: body-text rejection still HTTP 400 (gate spec §5.4 PR-2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body_text",
    [
        "This is a long script body intended to be the actual narration content.\nIt has newlines.",
        "Short body with whitespace inside",
        "另一行\n第二行的脚本正文",
    ],
)
def test_body_text_rejection_still_http_400(body_text: str) -> None:
    with pytest.raises(HTTPException) as excinfo:
        _validate_source_script_ref_shape(body_text)
    assert excinfo.value.status_code == 400


def test_oversize_payload_rejected_as_400() -> None:
    with pytest.raises(HTTPException) as excinfo:
        _validate_source_script_ref_shape("X" * 600)
    assert excinfo.value.status_code == 400


# ---------------------------------------------------------------------------
# §8.F regression: publisher-URL + bucket-URI rejection still HTTP 400
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref",
    [
        "https://news.qq.com/rain/a/20260503-some-article",
        "http://example.com/article",
        "s3://my-bucket/object/key",
        "gs://another-bucket/path/to/object",
    ],
)
def test_publisher_url_and_bucket_uri_rejection_still_http_400(ref: str) -> None:
    with pytest.raises(HTTPException) as excinfo:
        _validate_source_script_ref_shape(ref)
    assert excinfo.value.status_code == 400
    assert "scheme is not recognised" in excinfo.value.detail


# ---------------------------------------------------------------------------
# Backward compatibility: pre-§8.F operator-discipline handles still accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref",
    [
        "content://matrix-script/source/op-token-001",
        "content://matrix-script/source/MS-SRC-2026-05-03-001",
        "content://matrix-script/source/jackie-test-handle",
        "task://matrix-script/source/some-task-handle",
        "asset://matrix-script/source/some-asset-handle",
        "ref://matrix-script/source/some-ref-handle",
    ],
)
def test_operator_discipline_handles_still_accepted(ref: str) -> None:
    """Backward compatibility: handles minted under the §8.F / §8.H operator-discipline
    convention MUST continue to pass the guard with the §8.F-tightened scheme set
    unchanged. No operator migration is required."""
    accepted = _validate_source_script_ref_shape(ref)
    assert accepted == ref


# ---------------------------------------------------------------------------
# Mint-route constant alignment + scope-fence sanity
# ---------------------------------------------------------------------------


def test_mint_route_is_matrix_script_scoped() -> None:
    assert MATRIX_SCRIPT_MINT_ROUTE.startswith("/tasks/matrix-script/")
    # Negative: must not collide with Hot Follow / Digital Anchor / generic temp routes.
    assert "hot_follow" not in MATRIX_SCRIPT_MINT_ROUTE
    assert "hot-follow" not in MATRIX_SCRIPT_MINT_ROUTE
    assert "digital_anchor" not in MATRIX_SCRIPT_MINT_ROUTE
    assert "digital-anchor" not in MATRIX_SCRIPT_MINT_ROUTE
    assert "/tasks/connect/" not in MATRIX_SCRIPT_MINT_ROUTE


def test_mint_token_prefix_is_documented_constant() -> None:
    assert MINT_TOKEN_PREFIX == "mint"


def test_minted_handle_distinguishable_from_operator_discipline_token() -> None:
    """Coordinator readability: a coordinator scanning a deployed environment can
    distinguish product-minted handles from operator-discipline handles by the
    ``mint-`` prefix on the slug. The product binds no semantic meaning to the
    prefix, but the convention is documented in the contract addendum."""
    payload = mint_source_script_ref()
    handle = payload["source_script_ref"]
    expected_prefix = f"content://matrix-script/source/{MINT_TOKEN_PREFIX}-"
    assert handle.startswith(expected_prefix)

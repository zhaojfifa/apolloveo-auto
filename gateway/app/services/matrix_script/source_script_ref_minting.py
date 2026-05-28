"""Matrix Script Option F2 — in-product ``content://`` minting service.

Plan E PR-2 / Item E.MS.2: replaces the operator-discipline ``<token>``
convention pinned by §8.F / §8.H of the Plan A trial brief
(``docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`` §0.2) with a
product-owned minting flow that allocates an opaque
``content://matrix-script/source/<token>`` handle on operator request.

Discipline (binding):

- The product owns ``<token>`` allocation; operators no longer choose ``<token>``
  themselves. The handle is opaque to downstream code (per §0.2 product-meaning)
  — the product still does not dereference the handle to body content within
  this Plan E phase.
- Backward compatibility: handles minted under the operator-discipline
  convention (e.g. ``content://matrix-script/source/op-token-001``) remain valid
  and pass the §8.A guard with the §8.F-tightened scheme set unchanged. This
  service does NOT widen ``SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES``; it mints into
  the existing ``content://`` opaque-by-construction scheme only.
- No I/O across runtime boundaries; no provider/vendor lookup; no asset-library
  backend; no operator-supplied input dereferencing; no packet mutation; no
  publisher-URL ingestion; no body-input handling. The minting service is a
  pure local function that produces a fresh opaque token and wraps it in the
  closed ``content://`` URI.

Authority:

- ``docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md`` §3.2 / §5.2
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)"
  — specifically the ``Operator transitional convention`` sub-section that
  names Option F2 as the eventual minting-service resolution path.
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)"
  (additive sub-section landed in this PR).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Mapping
from uuid import uuid4

from gateway.app.services.matrix_script.create_entry import (
    SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES,
    _validate_source_script_ref_shape,
)
from gateway.app.services.matrix_script.source_script_body_store import (
    BODY_MAX_BYTES,
    SOURCE_KIND_PASTE,
    SOURCE_KIND_UPLOAD,
    SOURCE_KIND_VALUES,
    BodyStoreError,
    put_body,
)

MATRIX_SCRIPT_MINT_ROUTE = "/tasks/matrix-script/source-script-refs/mint"
MATRIX_SCRIPT_INGEST_ROUTE = "/tasks/matrix-script/source-script-refs/ingest"
MATRIX_SCRIPT_PEEK_ROUTE = "/tasks/matrix-script/source-script-refs/{token}/peek"
MINTING_POLICY = "operator_request_v1"
INGESTING_POLICY = "operator_body_ingest_v1"
MINT_TOKEN_PREFIX = "mint"
_MINT_TOKEN_HEX_LENGTH = 16
_REQUESTED_BY_MAX_LENGTH = 120
_REQUESTED_BY_PATTERN = re.compile(r"^[A-Za-z0-9._\-:/ ]+$")


def _mint_token() -> str:
    """Allocate an opaque, product-owned token suitable for the closed ``content://`` scheme.

    The token is a uuid-derived hex slug prefixed with a literal ``mint-`` so a
    coordinator scanning a deployed environment can distinguish product-minted
    handles from operator-discipline handles at a glance. The product never
    binds any meaning to the prefix or the slug — the handle remains opaque to
    every downstream consumer (per the §0.2 product-meaning of
    ``source_script_ref``).
    """

    slug = uuid4().hex[:_MINT_TOKEN_HEX_LENGTH]
    return f"{MINT_TOKEN_PREFIX}-{slug}"


def _coerce_requested_by(value: object | None) -> str:
    """Sanitize an optional ``requested_by`` operator note.

    The value is a record-keeping string only; the product does not dereference
    it, never returns it as packet truth, and never attaches it to any minted
    handle. Empty / non-string / oversize values collapse to the empty string.
    Non-printable / unsupported characters are rejected to keep the field a
    simple operator handle (same alphabet discipline as the bare-token path of
    ``_validate_source_script_ref_shape``).
    """

    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    if not cleaned:
        return ""
    if len(cleaned) > _REQUESTED_BY_MAX_LENGTH:
        cleaned = cleaned[:_REQUESTED_BY_MAX_LENGTH]
    if not _REQUESTED_BY_PATTERN.match(cleaned):
        return ""
    return cleaned


def mint_source_script_ref(*, requested_by: object | None = None) -> Mapping[str, str]:
    """Mint a fresh opaque ``content://matrix-script/source/<token>`` handle.

    Returns a mapping with the closed key set
    ``{"source_script_ref", "token", "minted_at", "policy", "requested_by"}``.

    The minted ``source_script_ref`` is **guaranteed** to pass the existing
    ``_validate_source_script_ref_shape`` guard with the §8.F-tightened scheme
    set — the contract acceptance for this PR. The function never raises, never
    performs I/O, and never widens the closed scheme set.
    """

    token = _mint_token()
    handle = f"content://matrix-script/source/{token}"
    # Guard alignment is contract acceptance — the minted handle MUST be
    # accepted by the same validator any operator-supplied handle goes through.
    # The validator raises HTTPException on failure; on success it returns the
    # value verbatim. We pin the assertion here so a future refactor of the
    # token shape that breaks the guard cannot ship.
    accepted = _validate_source_script_ref_shape(handle)
    minted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "source_script_ref": accepted,
        "token": token,
        "minted_at": minted_at,
        "policy": MINTING_POLICY,
        "requested_by": _coerce_requested_by(requested_by),
    }


def mint_source_script_ref_with_body(
    *,
    body_text: str,
    source_kind: str,
    requested_by: object | None = None,
) -> Mapping[str, object]:
    """Mint a fresh handle AND store the operator-supplied body text.

    Companion to :func:`mint_source_script_ref` for the 2026-05-28 Matrix
    Script Operator UI Redesign wave. The operator pastes a script body
    (or uploads a script document, parsed to text client-side) and this
    function:

    1. Allocates a fresh opaque ``content://matrix-script/source/<token>``
       handle via :func:`mint_source_script_ref` (no widening of the
       closed scheme set).
    2. Stores the body text in the in-process
       :mod:`source_script_body_store` keyed by the new ``token``.
    3. Returns the same closed-key envelope as ``mint_source_script_ref``
       plus three additive integer / string fields describing the stored
       body (``body_char_count`` / ``body_byte_size`` / ``body_source_kind``)
       and a flag ``has_body=True`` so callers can distinguish ingested
       handles from bare-mint handles.

    The body store is in-process and volatile — gateway restart clears it.
    The packet still carries only the opaque handle; the body never enters
    packet truth, never reaches any provider/model/vendor/engine, and is
    not durably persisted.

    Raises :class:`fastapi.HTTPException` (HTTP 400) on body validation
    failure (empty / oversize / unknown source_kind) via
    :class:`BodyStoreError` translation at the route boundary; this
    function itself raises :class:`BodyStoreError` directly so it remains
    HTTP-framework-agnostic.
    """

    if source_kind not in SOURCE_KIND_VALUES:
        raise BodyStoreError(
            f"source_kind={source_kind!r} not in closed set {sorted(SOURCE_KIND_VALUES)}"
        )
    # Allocate handle first — re-uses the existing minting discipline +
    # validator round-trip. If minting fails for any reason the body is
    # never stored.
    mint_payload = dict(mint_source_script_ref(requested_by=requested_by))
    record = put_body(
        token=mint_payload["token"],
        body_text=body_text,
        source_kind=source_kind,
        requested_by=mint_payload.get("requested_by", ""),
    )
    mint_payload.update(
        {
            "policy": INGESTING_POLICY,
            "has_body": True,
            "body_char_count": record.char_count,
            "body_byte_size": record.byte_size,
            "body_source_kind": record.source_kind,
        }
    )
    return mint_payload


__all__ = [
    "BODY_MAX_BYTES",
    "INGESTING_POLICY",
    "MATRIX_SCRIPT_INGEST_ROUTE",
    "MATRIX_SCRIPT_MINT_ROUTE",
    "MATRIX_SCRIPT_PEEK_ROUTE",
    "MINTING_POLICY",
    "MINT_TOKEN_PREFIX",
    "SOURCE_KIND_PASTE",
    "SOURCE_KIND_UPLOAD",
    "SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES",
    "mint_source_script_ref",
    "mint_source_script_ref_with_body",
]

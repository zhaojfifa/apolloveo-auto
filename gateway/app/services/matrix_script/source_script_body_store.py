"""Matrix Script · in-process source-script body store.

Companion to :mod:`source_script_ref_minting`. The mint service allocates an
opaque ``content://matrix-script/source/<token>`` handle but does not store
any body content. This module pairs a minted ``token`` with the body text
the operator pasted or uploaded so that downstream operator-facing surfaces
(notably Workbench Block B 脚本结构) can render real script content instead
of ``STATUS_UNRESOLVED`` sentinels.

Discipline (binding under the 2026-05-28 Matrix Script Operator UI
Redesign wave):

- **In-process / volatile.** Body text lives in a process-wide
  ``dict[str, BodyRecord]``; gateway restart clears the store. This
  mirrors the :class:`InMemoryClosureStore` pattern (Recovery Decision
  §4.3 known limit). No DB, no Redis, no file persistence.
- **No external I/O.** The store never sends body content to any
  provider, model, vendor, or engine. It is local memory only.
- **No packet mutation.** ``source_script_ref`` remains opaque to the
  packet layer per §0.2 product-meaning. The store is read by
  presenter helpers; it never writes to the task packet.
- **No widening of the accepted scheme set.** Bodies are only ever
  paired with tokens minted by :mod:`source_script_ref_minting` — i.e.
  ``content://matrix-script/source/<mint-token>`` handles. Pre-§8.F
  operator-discipline handles remain accepted at the entry validator
  but do NOT receive body storage through this service (operators
  paste body OR supply a pre-existing handle, never both).
- **No provider/model/vendor/engine identifier ever flows through
  this module.**

The store is intentionally simple: one ``put`` and one ``get`` plus a
``peek`` operator returning a sanitised summary. It is NOT a content
repository, NOT an asset library, NOT a CMS. Future Asset Library /
Plan E waves replace it with durable storage; this module is the
minimum honest backing the UI redesign needs so paste / upload is not
a fake operator affordance.

Authority pointer: 2026-05-28 Matrix Script Operator UI Redesign mission
(this wave); ``docs/contracts/matrix_script/task_entry_contract_v1.md``
§"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)"
opaque-handle product meaning preserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Mapping, Optional

# Upper bound for stored body text. Operators pasting a one-pager script
# rarely exceed this; the limit exists to keep the in-process store from
# absorbing arbitrarily large blobs while we have no durable backend.
BODY_MAX_BYTES = 64 * 1024  # 64 KB
BODY_CHAR_SOFT_LIMIT = 20000

# Closed source-of-body kinds. Recorded for coordinator audit (e.g. did
# the operator paste body or upload a file). Not exposed as packet truth.
SOURCE_KIND_PASTE = "operator_paste"
SOURCE_KIND_UPLOAD = "operator_upload"
SOURCE_KIND_VALUES = frozenset({SOURCE_KIND_PASTE, SOURCE_KIND_UPLOAD})


class BodyStoreError(ValueError):
    """Raised when ``put_body`` is called with an invalid argument."""


@dataclass(frozen=True)
class BodyRecord:
    """One stored body record. Frozen so callers cannot mutate it in place."""

    token: str
    body_text: str
    source_kind: str
    stored_at: str
    byte_size: int
    char_count: int
    requested_by: str = ""

    def to_peek(self) -> Mapping[str, object]:
        """Return a sanitised peek payload safe for operator-visible display.

        The peek payload includes the body text verbatim — that is the point
        of the body store. The caller is responsible for routing the peek
        only to operator surfaces (Workbench Block B) and never to
        contract-bound packet truth.
        """

        return {
            "token": self.token,
            "body_text": self.body_text,
            "source_kind": self.source_kind,
            "stored_at": self.stored_at,
            "byte_size": self.byte_size,
            "char_count": self.char_count,
            "requested_by": self.requested_by,
        }


class _SourceScriptBodyStore:
    """Thread-safe in-process store mapping ``token → BodyRecord``."""

    def __init__(self) -> None:
        self._records: Dict[str, BodyRecord] = {}
        self._lock = Lock()

    def put(
        self,
        *,
        token: str,
        body_text: str,
        source_kind: str,
        requested_by: str = "",
    ) -> BodyRecord:
        if not isinstance(token, str) or not token.strip():
            raise BodyStoreError("token must be a non-empty string")
        if not isinstance(body_text, str):
            raise BodyStoreError("body_text must be a string")
        if not body_text.strip():
            raise BodyStoreError("body_text must not be empty or whitespace-only")
        byte_size = len(body_text.encode("utf-8"))
        if byte_size > BODY_MAX_BYTES:
            raise BodyStoreError(
                f"body exceeds {BODY_MAX_BYTES} bytes ({byte_size} given); "
                "use a shorter sample or split the script."
            )
        if source_kind not in SOURCE_KIND_VALUES:
            raise BodyStoreError(
                f"source_kind={source_kind!r} not in closed set {sorted(SOURCE_KIND_VALUES)}"
            )
        record = BodyRecord(
            token=token.strip(),
            body_text=body_text,
            source_kind=source_kind,
            stored_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            byte_size=byte_size,
            char_count=len(body_text),
            requested_by=requested_by or "",
        )
        with self._lock:
            self._records[record.token] = record
        return record

    def get(self, token: str) -> Optional[BodyRecord]:
        if not isinstance(token, str):
            return None
        with self._lock:
            return self._records.get(token.strip())

    def peek(self, token: str) -> Optional[Mapping[str, object]]:
        record = self.get(token)
        if record is None:
            return None
        return record.to_peek()

    def has(self, token: str) -> bool:
        return self.get(token) is not None

    def clear(self) -> None:
        """Test-only / coordinator-only convenience to reset the store."""

        with self._lock:
            self._records.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._records)


# Process-wide singleton. Tests reset via ``_STORE.clear()`` in fixtures.
_STORE = _SourceScriptBodyStore()


def put_body(
    *,
    token: str,
    body_text: str,
    source_kind: str,
    requested_by: str = "",
) -> BodyRecord:
    """Store an operator-paste / operator-upload body keyed by ``token``."""

    return _STORE.put(
        token=token,
        body_text=body_text,
        source_kind=source_kind,
        requested_by=requested_by,
    )


def get_body(token: str) -> Optional[BodyRecord]:
    """Return the stored body record for ``token`` or ``None`` if absent."""

    return _STORE.get(token)


def peek_body(token: str) -> Optional[Mapping[str, object]]:
    """Return the sanitised peek payload for ``token`` or ``None``."""

    return _STORE.peek(token)


def has_body(token: str) -> bool:
    """Return ``True`` iff ``token`` has a stored body."""

    return _STORE.has(token)


def _reset_store_for_tests() -> None:
    """Reset the process-wide store. Test fixtures only."""

    _STORE.clear()


def _store_size() -> int:
    """Return the number of stored body records. Diagnostics only."""

    return _STORE.size()


__all__ = [
    "BODY_CHAR_SOFT_LIMIT",
    "BODY_MAX_BYTES",
    "BodyRecord",
    "BodyStoreError",
    "SOURCE_KIND_PASTE",
    "SOURCE_KIND_UPLOAD",
    "SOURCE_KIND_VALUES",
    "_reset_store_for_tests",
    "_store_size",
    "get_body",
    "has_body",
    "peek_body",
    "put_body",
]

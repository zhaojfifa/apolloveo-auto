"""Capability adapter base interfaces — donor-free P1 skeleton (B6).

Each ``*Adapter`` here is a thin abstract surface naming the capability kind
it serves and the invocation contract it accepts. Vendor implementations live
in ``gateway/app/services/workers/adapters/<vendor>/`` and MUST subclass the
matching adapter here. Provider SDK code stays in
``gateway/app/services/providers/<vendor>/`` and is composed *into* the
vendor adapter — never imported here.

Boundary discipline:
- ``capability_kind`` is drawn from the closed set in
  ``factory_packet_validator_rules_v1.md`` R3 (mirrored as ``AdapterCapabilityKind``).
- ``AdapterInvocation`` carries only contract-shaped inputs / outputs; no
  vendor / model / engine identifiers, in line with R3 vendor-pin prohibition.
- ``invoke`` is declared abstract; the base raises ``NotImplementedError`` so a
  donor-less import never produces side effects.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Union

from gateway.app.services.packet.envelope import CAPABILITY_KINDS

AdapterCapabilityKind = str  # constrained at runtime to CAPABILITY_KINDS


class AdapterErrorCategory(str, Enum):
    """Closed, provider-agnostic error categories for ``AdapterError``.

    Categories describe *shape of failure*, not vendor-specific error codes.
    A provider adapter MUST translate its native errors into one of these
    categories at its own boundary; provider-specific codes belong only in
    ``AdapterError.details``.
    """

    INVALID_INVOCATION = "invalid_invocation"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    AUTH = "auth"
    RATE_LIMITED = "rate_limited"
    UPSTREAM = "upstream"
    INTERNAL = "internal"


class AdapterError(Exception):
    """Base-only error envelope raised by adapters.

    Provider-agnostic on purpose:
    - MUST NOT carry vendor / model / engine identifiers as first-class fields
      (free-form provider codes may sit inside ``details`` only).
    - MUST NOT encode business truth (no task/packet/state semantics).
    - MUST NOT carry UI / presenter wording — ``message`` is a developer-facing
      diagnostic, not a user-facing string.
    - Advisory-shaped: callers surface this through ``AdapterResult.advisories``
      or equivalent, never as primary truth (cf. W2 admission Phase A
      ``test_fallback_never_primary_truth``).

    ``retryable`` is an *advisory hint* only. Actual retry policy is owned by
    the (future) base-only retry/timeout/cancellation surface (B2); this hint
    does not by itself authorise a retry.
    """

    __slots__ = ("category", "message", "source", "retryable", "details")

    def __init__(
        self,
        category: Union["AdapterErrorCategory", str],
        message: str,
        *,
        source: Optional[str] = None,
        retryable: Optional[bool] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if isinstance(category, AdapterErrorCategory):
            normalised = category
        else:
            try:
                normalised = AdapterErrorCategory(category)
            except ValueError as exc:
                raise ValueError(
                    f"AdapterError category '{category}' is not in the closed "
                    f"set {[c.value for c in AdapterErrorCategory]}"
                ) from exc
        if not isinstance(message, str) or not message:
            raise ValueError("AdapterError message must be a non-empty string")
        if source is not None and not isinstance(source, str):
            raise TypeError("AdapterError source must be a string when set")
        if retryable is not None and not isinstance(retryable, bool):
            raise TypeError("AdapterError retryable must be a bool when set")

        self.category: AdapterErrorCategory = normalised
        self.message: str = message
        self.source: Optional[str] = source
        self.retryable: Optional[bool] = retryable
        self.details: Mapping[str, Any] = MappingProxyType(dict(details or {}))
        super().__init__(message)

    def to_dict(self) -> dict:
        """Stable serialisation shape — keys are frozen by this base."""
        return {
            "category": self.category.value,
            "message": self.message,
            "source": self.source,
            "retryable": self.retryable,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class AdapterInvocation:
    """Contract-shaped inputs handed to an adapter.

    ``inputs`` and ``outputs`` mirror the corresponding fields on a packet's
    ``capability_plan`` entry. ``mode`` / ``quality_hint`` / ``language_hint``
    are optional advisory fields. ``extras`` carries forward-compatible keys
    but MUST NOT contain vendor / model / engine identifiers (R3).
    """

    capability_kind: AdapterCapabilityKind
    inputs: Optional[Mapping[str, Any]] = None
    outputs: Optional[Mapping[str, Any]] = None
    mode: Optional[str] = None
    quality_hint: Optional[str] = None
    language_hint: Optional[str] = None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterResult:
    """Contract-shaped output returned by an adapter.

    Adapters return artefact references and advisories; they never write
    truth state and never return raw vendor responses.
    """

    artefacts: Mapping[str, Any] = field(default_factory=dict)
    advisories: tuple = ()
    rule_versions: Mapping[str, str] = field(default_factory=dict)


class AdapterBase(abc.ABC):
    """Abstract capability adapter.

    Subclasses pin a single ``capability_kind`` from ``CAPABILITY_KINDS`` and
    implement ``invoke``. The base layer performs no I/O.
    """

    capability_kind: AdapterCapabilityKind = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        kind = getattr(cls, "capability_kind", "")
        if kind and kind not in CAPABILITY_KINDS:
            raise ValueError(
                f"adapter {cls.__name__} declares capability_kind '{kind}' "
                f"outside closed set {sorted(CAPABILITY_KINDS)}"
            )

    @abc.abstractmethod
    def invoke(self, invocation: AdapterInvocation) -> AdapterResult:
        """Execute the capability against ``invocation``. Vendor-specific."""
        raise NotImplementedError


class UnderstandingAdapter(AdapterBase):
    capability_kind = "understanding"


class SubtitlesAdapter(AdapterBase):
    capability_kind = "subtitles"


class DubAdapter(AdapterBase):
    capability_kind = "dub"


class VideoGenAdapter(AdapterBase):
    capability_kind = "video_gen"


class AvatarAdapter(AdapterBase):
    capability_kind = "avatar"


class FaceSwapAdapter(AdapterBase):
    capability_kind = "face_swap"


class PostProductionAdapter(AdapterBase):
    capability_kind = "post_production"


class PackAdapter(AdapterBase):
    capability_kind = "pack"


__all__ = [
    "AdapterBase",
    "AdapterCapabilityKind",
    "AdapterError",
    "AdapterErrorCategory",
    "AdapterInvocation",
    "AdapterResult",
    "UnderstandingAdapter",
    "SubtitlesAdapter",
    "DubAdapter",
    "VideoGenAdapter",
    "AvatarAdapter",
    "FaceSwapAdapter",
    "PostProductionAdapter",
    "PackAdapter",
]

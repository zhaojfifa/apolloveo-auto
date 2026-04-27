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
class SecretRef:
    """Logical, provider-agnostic handle to a single secret value.

    ``name`` is an adapter-defined logical key. It MUST NOT be an env var
    name, a vendor-pinned token id, or a credential literal — mapping a
    logical name to its concrete source (env, vault, KMS, file) is the
    resolver's responsibility, not the base's. Concrete env-name authority
    lives in ``ops/env/env_matrix_v1.md`` (W2 admission Phase B).

    ``purpose`` is an optional, human-readable annotation (e.g. "translate
    api key"). It carries no truth and no vendor identifier.
    """

    name: str
    purpose: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("SecretRef.name must be a non-empty string")
        if self.purpose is not None and not isinstance(self.purpose, str):
            raise TypeError("SecretRef.purpose must be a string when set")


class SecretResolver(abc.ABC):
    """Provider-agnostic resolver of logical ``SecretRef`` handles.

    The base only declares this surface; it does **not** ship an
    implementation. Concrete resolvers live in the runtime / ops layer
    (outside this base module), so the adapter base never grows a direct
    dependency on env-loading, vault clients, or vendor SDKs.

    Discipline:
    - MUST NOT be implemented inside ``capability/adapters/`` itself.
    - MUST be side-effect-free at construction (no I/O at ``__init__``).
    - ``resolve`` MAY perform I/O; it returns the secret value or ``None``
      when absent. Fail-closed semantics belong to the caller per
      ``ops/env/secret_loading_baseline_v1.md`` §3.5.
    """

    @abc.abstractmethod
    def resolve(self, ref: "SecretRef") -> Optional[str]:
        """Return the secret value bound to ``ref`` or ``None`` if absent."""
        raise NotImplementedError


@dataclass(frozen=True)
class AdapterCredentials:
    """Construction-time credential surface handed to an adapter.

    Holds an injected ``SecretResolver``. Provider-agnostic on purpose:
    - MUST NOT carry vendor / model / engine identifiers.
    - MUST NOT carry resolved secret values (the value lives only inside
      ``resolver.resolve(...)`` calls at invocation time).
    - MUST NOT carry env var names — those are resolver-internal.
    - MUST NOT encode business / task / packet truth.

    The base never calls ``resolver.resolve(...)`` itself; resolution is
    the vendor adapter's job at invocation time.
    """

    resolver: SecretResolver

    def __post_init__(self) -> None:
        if not isinstance(self.resolver, SecretResolver):
            raise TypeError(
                "AdapterCredentials.resolver must be a SecretResolver instance"
            )


class CancellationToken(abc.ABC):
    """Provider-agnostic cancellation signal.

    The base ships only the abstract surface; it does **not** ship a
    concrete token (manual, deadline-driven, parent-linked). Concrete
    tokens live in the runtime / caller layer outside this base, so the
    adapter base never grows a direct dependency on a specific async
    framework, scheduler, or provider client.

    Discipline:
    - MUST be side-effect-free at construction (no I/O at ``__init__``).
    - ``is_cancelled`` MUST be cheap and side-effect-free.
    - The base never authors cancellation truth; it only reads the
      signal a caller hands in via ``AdapterExecutionContext``.
    """

    @property
    @abc.abstractmethod
    def is_cancelled(self) -> bool:
        """Return ``True`` if the operation has been cancelled."""
        raise NotImplementedError

    def raise_if_cancelled(self) -> None:
        """Raise ``AdapterError(CANCELLED)`` if the token is cancelled.

        Provided as a small base-only convenience so callers raise a
        consistent, provider-agnostic error shape. Subclasses MUST NOT
        override this with provider-specific exception types.
        """
        if self.is_cancelled:
            raise AdapterError(
                AdapterErrorCategory.CANCELLED,
                "execution cancelled before completion",
            )


@dataclass(frozen=True)
class RetryPolicy:
    """Provider-agnostic retry advisory shape.

    Carries hints only — does NOT bind to any third-party retry library
    or vendor SDK retry helper, does NOT encode provider-specific
    backoff tuning, and does NOT itself execute the retry. The (future)
    caller / runtime layer owns the retry loop.

    Discipline:
    - MUST NOT carry vendor / model / engine identifiers.
    - MUST NOT encode jitter / scheduling primitives — those belong to
      the caller layer, not the base envelope.
    - ``max_attempts`` counts *total* attempts (initial try + retries),
      so ``1`` means "no retry".
    """

    max_attempts: int = 1
    initial_backoff_seconds: float = 0.0
    max_backoff_seconds: float = 0.0
    backoff_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.max_attempts, int)
            or isinstance(self.max_attempts, bool)
            or self.max_attempts < 1
        ):
            raise ValueError(
                "RetryPolicy.max_attempts must be an int >= 1"
            )
        for fname in ("initial_backoff_seconds", "max_backoff_seconds"):
            value = getattr(self, fname)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            ):
                raise ValueError(
                    f"RetryPolicy.{fname} must be a non-negative number"
                )
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError(
                "RetryPolicy.max_backoff_seconds must be >= initial_backoff_seconds"
            )
        if (
            isinstance(self.backoff_multiplier, bool)
            or not isinstance(self.backoff_multiplier, (int, float))
            or self.backoff_multiplier < 1.0
        ):
            raise ValueError(
                "RetryPolicy.backoff_multiplier must be a number >= 1.0"
            )


@dataclass(frozen=True)
class AdapterExecutionContext:
    """Per-invocation execution control envelope.

    Provider-agnostic on purpose:
    - MUST NOT carry vendor / model / engine identifiers.
    - MUST NOT bind to any specific retry library or async framework.
    - MUST NOT encode business / task / packet truth.
    - MUST NOT carry presenter / UI wording.
    - MUST NOT carry fallback strategy — fallback is a business-layer
      concern (cf. W2 admission Phase A
      ``test_fallback_never_primary_truth``).

    Fields are advisory inputs to the (future) caller / runtime layer
    that drives timing, retries, and cancellation around ``invoke``.
    The base never starts timers, never schedules retries, and never
    polls cancellation itself — it only carries the shape.
    """

    timeout_seconds: Optional[float] = None
    cancellation: Optional[CancellationToken] = None
    retry: Optional[RetryPolicy] = None

    def __post_init__(self) -> None:
        if self.timeout_seconds is not None:
            if (
                isinstance(self.timeout_seconds, bool)
                or not isinstance(self.timeout_seconds, (int, float))
                or self.timeout_seconds <= 0
            ):
                raise ValueError(
                    "AdapterExecutionContext.timeout_seconds must be a positive "
                    "number when set"
                )
        if self.cancellation is not None and not isinstance(
            self.cancellation, CancellationToken
        ):
            raise TypeError(
                "AdapterExecutionContext.cancellation must be a "
                "CancellationToken instance when set"
            )
        if self.retry is not None and not isinstance(self.retry, RetryPolicy):
            raise TypeError(
                "AdapterExecutionContext.retry must be a RetryPolicy "
                "instance when set"
            )


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

    def __init__(
        self, *, credentials: Optional[AdapterCredentials] = None
    ) -> None:
        """Base-only construction surface.

        Accepts an optional ``AdapterCredentials`` envelope and stores it for
        later invocation-time use by the vendor adapter. The base performs
        no I/O here and never calls ``credentials.resolver.resolve(...)`` —
        secret resolution is the vendor adapter's responsibility at invoke
        time. Construction-vs-invocation lifecycle policy beyond this storage
        is deferred to the B4 PR.
        """
        if credentials is not None and not isinstance(
            credentials, AdapterCredentials
        ):
            raise TypeError(
                "credentials must be an AdapterCredentials instance"
            )
        self._credentials: Optional[AdapterCredentials] = credentials

    @property
    def credentials(self) -> Optional[AdapterCredentials]:
        """Read-only access to injected credentials (may be ``None``)."""
        return self._credentials

    @abc.abstractmethod
    def invoke(
        self,
        invocation: AdapterInvocation,
        *,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        """Execute the capability against ``invocation``. Vendor-specific.

        ``context`` is the unified base-only execution control entry
        (timeout / retry / cancellation hints). The base never inspects
        ``context`` itself; honouring it is the (future) caller / runtime
        and vendor adapter responsibility. Construction-vs-invocation
        lifecycle policy beyond this signature is deferred to the B4 PR.
        """
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
    "AdapterCredentials",
    "AdapterError",
    "AdapterErrorCategory",
    "AdapterExecutionContext",
    "AdapterInvocation",
    "AdapterResult",
    "CancellationToken",
    "RetryPolicy",
    "SecretRef",
    "SecretResolver",
    "UnderstandingAdapter",
    "SubtitlesAdapter",
    "DubAdapter",
    "VideoGenAdapter",
    "AvatarAdapter",
    "FaceSwapAdapter",
    "PostProductionAdapter",
    "PackAdapter",
]

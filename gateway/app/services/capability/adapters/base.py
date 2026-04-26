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
from typing import Any, Mapping, Optional

from gateway.app.services.packet.envelope import CAPABILITY_KINDS

AdapterCapabilityKind = str  # constrained at runtime to CAPABILITY_KINDS


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

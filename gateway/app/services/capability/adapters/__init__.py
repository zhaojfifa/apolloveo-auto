"""Capability adapter base interfaces (P1 skeleton, B6 delivery).

This package holds the **interface contracts** that every vendor adapter must
satisfy. It is intentionally donor-free: no SwiftCraft / Jellyfish code, no
provider clients, no runtime side effects.

Authority:
- Master Plan v1.1 Part IV.1 (Capability Supply mid-tier)
- ``docs/contracts/factory_packet_validator_rules_v1.md`` R3 (closed capability
  kind set; vendor pins forbidden at packet level)
- ``docs/contracts/worker_gateway_contract.md`` (worker invocation envelope)

Non-responsibilities:
- Does NOT import or wrap any vendor SDK or donor module.
- Does NOT decide routing; ``routing.py`` consumes adapters via the registry.
- Does NOT carry truth state; adapters are pure invocation surfaces.
- Does NOT pin ``vendor_id`` / ``model_id`` at the adapter base layer.
"""
from .base import (
    AdapterBase,
    AdapterCapabilityKind,
    AdapterInvocation,
    AdapterResult,
    AvatarAdapter,
    DubAdapter,
    FaceSwapAdapter,
    PackAdapter,
    PostProductionAdapter,
    SubtitlesAdapter,
    UnderstandingAdapter,
    VideoGenAdapter,
)

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

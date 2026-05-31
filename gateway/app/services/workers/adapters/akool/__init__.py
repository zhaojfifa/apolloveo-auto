"""Akool worker-side adapter bindings — SKELETON ONLY (PR-1, rows P-01 / P-02).

Binds the ``gateway/app/services/providers/akool/`` skeleton client into
capability adapter base interfaces under
``gateway/app/services/capability/adapters/``.

PR-1 scope (hard boundary): skeleton bindings for ``VideoGenAdapter`` /
``AvatarAdapter`` / ``FaceSwapAdapter`` only — no live call, no polling
runtime, no webhook, no Matrix Script / Delivery wiring, no ``final.mp4``
generation, no provider URL as deliverable. Real generation is gated behind
Capability Expansion W2.3.
"""
from ._common import (
    AKOOL_API_KEY_REF,
    AKOOL_BASE_URL_REF,
    AKOOL_LOGICAL_TO_ENV,
    AkoolAdapterSkeletonMixin,
    map_akool_error,
    resolve_config,
)
from .avatar import AkoolAvatarAdapter
from .face_swap import AkoolFaceSwapAdapter
from .video_gen import AkoolVideoGenAdapter

__all__ = [
    "AKOOL_API_KEY_REF",
    "AKOOL_BASE_URL_REF",
    "AKOOL_LOGICAL_TO_ENV",
    "AkoolAdapterSkeletonMixin",
    "AkoolAvatarAdapter",
    "AkoolFaceSwapAdapter",
    "AkoolVideoGenAdapter",
    "map_akool_error",
    "resolve_config",
]

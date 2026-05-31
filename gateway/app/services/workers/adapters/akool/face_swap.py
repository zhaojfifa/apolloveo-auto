"""Akool ↔ ``FaceSwapAdapter`` binding — SKELETON ONLY (PR-1).

Binds the Akool Face Swap capability behind the provider-agnostic
``FaceSwapAdapter`` surface. PR-1 ships no live call (no transport by default),
no polling loop, no media assembly, and never treats a provider URL as a
deliverable. See ``_common.py`` for the shared boundary statement.
"""
from __future__ import annotations

from typing import Optional

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    FaceSwapAdapter,
)
from gateway.app.services.providers.akool import AkoolCapability, AkoolTransport

from ._common import AkoolAdapterSkeletonMixin


class AkoolFaceSwapAdapter(AkoolAdapterSkeletonMixin, FaceSwapAdapter):
    """``FaceSwapAdapter`` bound to the Akool face-swap capability."""

    _akool_capability = AkoolCapability.FACE_SWAP
    _source = "akool.face_swap"

    def __init__(
        self,
        *,
        credentials: AdapterCredentials,
        transport: Optional[AkoolTransport] = None,
    ) -> None:
        super().__init__(credentials=credentials, transport=transport)

    def invoke(
        self,
        invocation: AdapterInvocation,
        *,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        return self._invoke_skeleton(
            invocation, expected_kind=self.capability_kind, context=context
        )

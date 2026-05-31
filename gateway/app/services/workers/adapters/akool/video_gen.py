"""Akool ↔ ``VideoGenAdapter`` binding — SKELETON ONLY (PR-1).

Binds the Akool Image-to-Video capability behind the provider-agnostic
``VideoGenAdapter`` surface. PR-1 ships no live call (no transport by default),
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
    VideoGenAdapter,
)
from gateway.app.services.providers.akool import AkoolCapability, AkoolTransport

from ._common import AkoolAdapterSkeletonMixin


class AkoolVideoGenAdapter(AkoolAdapterSkeletonMixin, VideoGenAdapter):
    """``VideoGenAdapter`` bound to the Akool image-to-video capability."""

    _akool_capability = AkoolCapability.IMAGE_TO_VIDEO
    _source = "akool.video_gen"

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

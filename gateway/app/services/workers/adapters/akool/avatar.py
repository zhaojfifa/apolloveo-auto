"""Akool ↔ ``AvatarAdapter`` binding — SKELETON ONLY (PR-1).

Binds the Akool Talking Avatar capability behind the provider-agnostic
``AvatarAdapter`` surface. PR-1 ships no live call (no transport by default),
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
    AvatarAdapter,
)
from gateway.app.services.providers.akool import AkoolCapability, AkoolTransport

from ._common import AkoolAdapterSkeletonMixin


class AkoolAvatarAdapter(AkoolAdapterSkeletonMixin, AvatarAdapter):
    """``AvatarAdapter`` bound to the Akool talking-avatar capability."""

    _akool_capability = AkoolCapability.TALKING_AVATAR
    _source = "akool.avatar"

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

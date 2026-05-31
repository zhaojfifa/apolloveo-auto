"""Akool provider client subpackage — SKELETON ONLY (PR-1, rows P-01 / P-02).

Side-effect-free at import: only the skeleton client + its typed surface are
exposed. This subpackage imports no HTTP library and owns no socket; it can
make no live call by construction (a transport must be injected, and PR-1
ships none). See ``client.py`` for the full hard-boundary statement.
"""
from .client import (
    AKOOL_SUCCESS_CODE,
    AkoolCapability,
    AkoolClient,
    AkoolClientConfig,
    AkoolCreateResult,
    AkoolError,
    AkoolErrorKind,
    AkoolHttpRequest,
    AkoolHttpResponse,
    AkoolTaskResult,
    AkoolTaskStatus,
    AkoolTransport,
    ProviderTemporaryOutput,
    classify_akool_code,
)

__all__ = [
    "AKOOL_SUCCESS_CODE",
    "AkoolCapability",
    "AkoolClient",
    "AkoolClientConfig",
    "AkoolCreateResult",
    "AkoolError",
    "AkoolErrorKind",
    "AkoolHttpRequest",
    "AkoolHttpResponse",
    "AkoolTaskResult",
    "AkoolTaskStatus",
    "AkoolTransport",
    "ProviderTemporaryOutput",
    "classify_akool_code",
]

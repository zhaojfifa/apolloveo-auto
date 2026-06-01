"""Akool real one-shot gate + guarded adapter invocation (PR-15R).

The trial-wave gate that decides whether a REAL Akool scene-clip generation is
permitted, and a guarded invocation that calls the PR-1 Akool adapter only when
the gate is open. **Default OFF**: with the feature flag unset (or no API key,
or no live transport) the system performs no provider call and reports a local
fallback decision.

Governance: real generation is the Capability Expansion Gate Wave (W2.3) scope
per the Phase 3 design plan §2/§10. This module ships the *mechanism* gated
behind an explicit, default-off feature flag; flipping it on (with a key + a
wired live transport) is a deliberate operator act, not the default. PR-15R
ships **no live transport**, so even "enabled" degrades to a graceful local
fallback unless a transport is explicitly injected.

Hard boundary (PR-15R):
- NO provider URL / Akool task id / model / credit in any returned
  operator-facing field. Decisions carry only closed reason codes + neutral,
  provider-agnostic Chinese operator text.
- NO official publish gate change; NO ``publish_url`` / ``publish_status``.
- NO artifact_storage / R2 write (staging is PR-16R); NO route (PR-17R).
- Provider temporary URLs are NEVER treated as deliverable here; a real output
  is flagged ``requires_staging=True`` for a later, separately-approved staging
  step, and its URL is not surfaced.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterError,
    AdapterInvocation,
    AdapterResult,
    SecretRef,
)
from gateway.app.services.workers.adapters.akool import (
    AKOOL_API_KEY_REF,
    AKOOL_LOGICAL_TO_ENV,
    AkoolVideoGenAdapter,
)
from gateway.app.services.workers.secrets import EnvSecretResolver

# Explicit, default-off feature flag. Real Akool calls are permitted only when
# this is truthy AND an api key is resolvable AND a live transport is injected.
AKOOL_REAL_FLAG_ENV = "MATRIX_SCRIPT_AKOOL_REAL"
_TRUTHY = frozenset({"1", "true", "yes", "on"})

# Closed reason codes (engineering-facing). Never surfaced as provider strings.
REASON_DISABLED_FLAG_OFF = "real_disabled_flag_off"
REASON_DISABLED_NO_KEY = "real_disabled_no_key"
REASON_ENABLED = "real_enabled"

# Closed guarded-invocation statuses.
STATUS_FALLBACK_LOCAL = "fallback_local"
STATUS_REAL_OK = "real_attempted_ok"
STATUS_REAL_BLOCKED = "real_blocked"

# Operator-safe Chinese text — provider-agnostic (no Akool / vendor / model).
_OP_FLAG_OFF = "实时生成能力未开启，使用本地兜底生成。"
_OP_NO_KEY = "实时生成所需凭据缺失，使用本地兜底生成。"
_OP_ENABLED = "实时生成能力已开启。"
_OP_REAL_OK = "实时生成已完成一个镜头，其余使用本地兜底。"
_OP_REAL_BLOCKED = "实时生成未成功，已回退本地兜底生成。"

# Tokens that must never leak into operator-facing decision fields.
_FORBIDDEN_TOKENS = (
    "akool", "provider", "vendor", "model_id", "credit",
    "provider_url", "temporary_url", "download_url", "provider_task_id",
    "artifact_key", "r2_key", "publish_url", "publish_status", "http://", "https://",
)


@dataclass(frozen=True)
class AkoolRealGateDecision:
    """Whether a real Akool call is permitted, with an operator-safe reason."""

    enabled: bool
    reason_code: str
    operator_reason_zh: str


@dataclass(frozen=True)
class GuardedInvocationResult:
    """Outcome of a guarded one-shot generation attempt.

    Operator-safe: no provider URL / task id / model / credit. A real output is
    flagged ``requires_staging`` (PR-16R copies it into Apollo storage); the URL
    itself is never carried here.
    """

    used_real_provider: bool
    fallback: bool
    status: str
    operator_reason_zh: str
    provider_output_present: bool = False
    requires_staging: bool = False
    blocked_reason_zh: Optional[str] = None


def _flag_enabled(env: Optional[Mapping[str, str]]) -> bool:
    src = env if env is not None else os.environ
    return str(src.get(AKOOL_REAL_FLAG_ENV, "")).strip().lower() in _TRUTHY


def _default_resolver() -> EnvSecretResolver:
    return EnvSecretResolver(AKOOL_LOGICAL_TO_ENV)


def _api_key_present(resolver: Any) -> bool:
    try:
        return bool(resolver.resolve(AKOOL_API_KEY_REF))
    except Exception:
        return False


def evaluate_akool_real_gate(
    *,
    env: Optional[Mapping[str, str]] = None,
    resolver: Any = None,
) -> AkoolRealGateDecision:
    """Evaluate the gate. Default OFF unless flag truthy AND api key present."""
    if not _flag_enabled(env):
        return AkoolRealGateDecision(False, REASON_DISABLED_FLAG_OFF, _OP_FLAG_OFF)
    res = resolver if resolver is not None else _default_resolver()
    if not _api_key_present(res):
        return AkoolRealGateDecision(False, REASON_DISABLED_NO_KEY, _OP_NO_KEY)
    return AkoolRealGateDecision(True, REASON_ENABLED, _OP_ENABLED)


def guarded_generate_one_shot(
    *,
    gate: AkoolRealGateDecision,
    invocation: AdapterInvocation,
    credentials: Optional[AdapterCredentials] = None,
    transport: Optional[Callable[..., Any]] = None,
) -> GuardedInvocationResult:
    """Invoke the real Akool adapter only when the gate is open.

    Gate closed → local fallback, NO adapter call. Gate open → call the PR-1
    ``AkoolVideoGenAdapter`` with the injected ``transport`` (PR-15R ships none,
    so an un-wired call degrades to a graceful ``real_blocked`` fallback). On any
    ``AdapterError`` → ``real_blocked`` fallback with an operator-safe reason.
    Provider URLs / ids are never surfaced.
    """
    if not isinstance(gate, AkoolRealGateDecision):
        raise TypeError("gate must be an AkoolRealGateDecision")
    if not gate.enabled:
        return GuardedInvocationResult(
            used_real_provider=False,
            fallback=True,
            status=STATUS_FALLBACK_LOCAL,
            operator_reason_zh=gate.operator_reason_zh,
        )
    if credentials is None:
        credentials = AdapterCredentials(resolver=_default_resolver())
    adapter = AkoolVideoGenAdapter(credentials=credentials, transport=transport)
    try:
        result = adapter.invoke(invocation)
    except AdapterError:
        # Operator-safe: do NOT surface provider category / message / url.
        return GuardedInvocationResult(
            used_real_provider=False,
            fallback=True,
            status=STATUS_REAL_BLOCKED,
            operator_reason_zh=_OP_REAL_BLOCKED,
            blocked_reason_zh=_OP_REAL_BLOCKED,
        )
    provider_output_present = bool(
        isinstance(result, AdapterResult)
        and result.artefacts.get("provider_output_present")
    )
    return GuardedInvocationResult(
        used_real_provider=True,
        fallback=False,
        status=STATUS_REAL_OK,
        operator_reason_zh=_OP_REAL_OK,
        provider_output_present=provider_output_present,
        # A real provider output must be staged into Apollo storage (PR-16R)
        # before it is ever a deliverable; its URL is not carried here.
        requires_staging=provider_output_present,
    )


def gate_decision_to_dict(decision: AkoolRealGateDecision) -> Dict[str, object]:
    payload = {
        "enabled": decision.enabled,
        "reason_code": decision.reason_code,
        "operator_reason_zh": decision.operator_reason_zh,
    }
    assert_no_gate_forbidden_tokens(payload)
    return payload


def guarded_result_to_dict(result: GuardedInvocationResult) -> Dict[str, object]:
    payload = {
        "used_real_provider": result.used_real_provider,
        "fallback": result.fallback,
        "status": result.status,
        "operator_reason_zh": result.operator_reason_zh,
        "provider_output_present": result.provider_output_present,
        "requires_staging": result.requires_staging,
        "blocked_reason_zh": result.blocked_reason_zh,
    }
    assert_no_gate_forbidden_tokens(payload)
    return payload


def assert_no_gate_forbidden_tokens(payload: object) -> None:
    """Raise if any provider/credit/url/publish token leaks into operator text.

    Note: the closed ``reason_code`` / ``status`` enums and the
    ``used_real_provider`` / ``provider_output_present`` keys intentionally use
    the word "provider" as a neutral, provider-AGNOSTIC field name; those keys
    are checked structurally, while VALUES must never carry a vendor name.
    """
    if isinstance(payload, dict):
        # values only (keys like ``used_real_provider`` are provider-agnostic)
        for value in payload.values():
            _scan_value(value)
    else:
        _scan_value(payload)


def _scan_value(value: object) -> None:
    text = str(value).lower()
    hits: List[str] = [t for t in _FORBIDDEN_TOKENS if t in text]
    if hits:
        raise ValueError(f"gate payload value leaks forbidden tokens: {hits}")

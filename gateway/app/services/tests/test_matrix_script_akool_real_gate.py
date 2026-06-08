"""Akool real one-shot gate + guarded invocation tests (PR-15R).

Proves: default OFF (no provider call), enabled requires flag + key, guarded
invocation never calls the provider when the gate is closed, real path is
sanitized (no provider URL/id/credit), failures degrade to an operator-safe
local fallback.
"""
from __future__ import annotations

import json
from typing import Any, List, Mapping, Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterInvocation,
    SecretRef,
    SecretResolver,
)
from gateway.app.services.matrix_script.akool_real_gate import (
    AKOOL_REAL_FLAG_ENV,
    REASON_DISABLED_FLAG_OFF,
    REASON_DISABLED_NO_KEY,
    REASON_ENABLED,
    STATUS_FALLBACK_LOCAL,
    STATUS_REAL_BLOCKED,
    STATUS_REAL_OK,
    AkoolRealGateDecision,
    assert_no_gate_forbidden_tokens,
    evaluate_akool_real_gate,
    gate_decision_to_dict,
    guarded_generate_one_shot,
    guarded_result_to_dict,
)
from gateway.app.services.providers.akool import AkoolHttpRequest, AkoolHttpResponse


class _Resolver(SecretResolver):
    def __init__(self, key: Optional[str]):
        self._key = key

    def resolve(self, ref: SecretRef) -> Optional[str]:
        return self._key


class _TransportSpy:
    def __init__(self, responses: Optional[List[AkoolHttpResponse]] = None):
        self.calls = 0
        self._responses = list(responses or [])

    def __call__(self, request: AkoolHttpRequest) -> AkoolHttpResponse:
        self.calls += 1
        return self._responses.pop(0)


def _invocation() -> AdapterInvocation:
    return AdapterInvocation(capability_kind="video_gen", inputs={"image_url": "x", "prompt": "y"})


def _success_transport() -> _TransportSpy:
    return _TransportSpy([
        AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "job-1", "status": 1}}),
        AkoolHttpResponse(200, {"code": 1000, "data": {"video_status": 3, "video": "https://tmp.akool/x.mp4"}}),
    ])


# ---------------------------------------------------------------------------
# gate evaluation (acceptance 1,2)
# ---------------------------------------------------------------------------


def test_gate_default_off_when_flag_unset() -> None:
    d = evaluate_akool_real_gate(env={}, resolver=_Resolver("k"))
    assert d.enabled is False and d.reason_code == REASON_DISABLED_FLAG_OFF


def test_gate_off_when_flag_on_but_no_key() -> None:
    d = evaluate_akool_real_gate(env={AKOOL_REAL_FLAG_ENV: "1"}, resolver=_Resolver(None))
    assert d.enabled is False and d.reason_code == REASON_DISABLED_NO_KEY


def test_gate_on_when_flag_and_key_present() -> None:
    d = evaluate_akool_real_gate(env={AKOOL_REAL_FLAG_ENV: "true"}, resolver=_Resolver("k"))
    assert d.enabled is True and d.reason_code == REASON_ENABLED


@pytest.mark.parametrize("val,expected", [("1", True), ("true", True), ("yes", True), ("on", True), ("0", False), ("false", False), ("", False), ("nope", False)])
def test_flag_truthiness(val, expected) -> None:
    d = evaluate_akool_real_gate(env={AKOOL_REAL_FLAG_ENV: val}, resolver=_Resolver("k"))
    assert d.enabled is expected


# ---------------------------------------------------------------------------
# guarded invocation (acceptance 1,3,8)
# ---------------------------------------------------------------------------


def test_guarded_disabled_does_not_call_provider() -> None:
    spy = _TransportSpy()
    gate = AkoolRealGateDecision(False, REASON_DISABLED_FLAG_OFF, "实时生成能力未开启，使用本地兜底生成。")
    r = guarded_generate_one_shot(gate=gate, invocation=_invocation(), transport=spy)
    assert r.used_real_provider is False and r.fallback is True and r.status == STATUS_FALLBACK_LOCAL
    assert spy.calls == 0  # provider never called when gate closed


def test_guarded_enabled_success_flags_staging_no_url_leak() -> None:
    gate = AkoolRealGateDecision(True, REASON_ENABLED, "实时生成能力已开启。")
    creds = AdapterCredentials(resolver=_Resolver("k"))
    r = guarded_generate_one_shot(gate=gate, invocation=_invocation(), credentials=creds, transport=_success_transport())
    assert r.used_real_provider is True and r.status == STATUS_REAL_OK
    assert r.provider_output_present is True and r.requires_staging is True
    blob = json.dumps(guarded_result_to_dict(r), ensure_ascii=False).lower()
    for token in ("akool", "http://", "https://", ".mp4", "provider_url", "publish_url", "credit"):
        assert token not in blob


def test_guarded_enabled_without_transport_falls_back_blocked() -> None:
    # PR-15R ships no live transport → un-wired call degrades gracefully.
    gate = AkoolRealGateDecision(True, REASON_ENABLED, "实时生成能力已开启。")
    creds = AdapterCredentials(resolver=_Resolver("k"))
    r = guarded_generate_one_shot(gate=gate, invocation=_invocation(), credentials=creds, transport=None)
    assert r.used_real_provider is False and r.fallback is True and r.status == STATUS_REAL_BLOCKED
    assert r.blocked_reason_zh and "兜底" in r.blocked_reason_zh


def test_guarded_enabled_quota_error_blocked_without_credit_leak() -> None:
    gate = AkoolRealGateDecision(True, REASON_ENABLED, "实时生成能力已开启。")
    creds = AdapterCredentials(resolver=_Resolver("k"))
    transport = _TransportSpy([AkoolHttpResponse(200, {"code": 1104, "msg": "insufficient credit balance: 0"})])
    r = guarded_generate_one_shot(gate=gate, invocation=_invocation(), credentials=creds, transport=transport)
    assert r.status == STATUS_REAL_BLOCKED and r.fallback is True
    blob = json.dumps(guarded_result_to_dict(r), ensure_ascii=False).lower()
    assert "credit" not in blob and "1104" not in blob and "akool" not in blob


# ---------------------------------------------------------------------------
# leakage guards (acceptance 7)
# ---------------------------------------------------------------------------


def test_decision_and_result_dicts_are_leak_free() -> None:
    gd = gate_decision_to_dict(evaluate_akool_real_gate(env={}, resolver=_Resolver("k")))
    for v in gd.values():
        s = str(v).lower()
        for token in ("akool", "provider_url", "publish_url", "http://", "https://", "credit", "model_id"):
            assert token not in s


def test_guard_rejects_injected_provider_value() -> None:
    with pytest.raises(ValueError):
        assert_no_gate_forbidden_tokens({"operator_reason_zh": "served by akool"})


def test_operator_reasons_have_no_provider_name() -> None:
    for env in ({}, {AKOOL_REAL_FLAG_ENV: "1"}):
        d = evaluate_akool_real_gate(env=env, resolver=_Resolver(None))
        assert "akool" not in d.operator_reason_zh.lower()
        assert "provider" not in d.operator_reason_zh.lower()


# ---------------------------------------------------------------------------
# import-boundary
# ---------------------------------------------------------------------------


def test_module_has_no_storage_or_publish_dependency() -> None:
    import inspect
    from gateway.app.services.matrix_script import akool_real_gate as mod
    src = inspect.getsource(mod)
    for token in (
        "import artifact_storage", "artifact_storage import", "upload_artifact(",
        "get_download_url(", "gateway.app.routers",
        "gateway.app.services.hot_follow", "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"gate module leaks into {token}"

"""Akool capability adapter skeleton tests (PR-1).

Covers ``gateway/app/services/workers/adapters/akool/`` (video_gen / avatar /
face_swap):

- subclass shape + invoke signature parity with the base
- B4 lifecycle: construction is I/O-free and resolves no secrets; ``invoke``
  is the first reachable surface that resolves credentials
- skeleton boundary: with no injected transport, ``invoke`` makes no live
  call and surfaces ``AdapterError(UNAVAILABLE)`` (NOT_WIRED mapped)
- B3 error mapping: ``AkoolErrorKind`` → closed ``AdapterErrorCategory``
- credit / quota signal is mapped to UNAVAILABLE with no credit figure leaked
- vendor leakage guard: the operator-bound ``AdapterResult`` carries no
  vendor / model / credit / secret token
- secret handling: missing key → AUTH; key resolved only at invoke time
"""
from __future__ import annotations

import inspect
from typing import Any, Dict, List, Mapping, Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterBase,
    AdapterCredentials,
    AdapterError,
    AdapterErrorCategory,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    AvatarAdapter,
    CancellationToken,
    FaceSwapAdapter,
    SecretRef,
    SecretResolver,
    VideoGenAdapter,
)
from gateway.app.services.providers.akool import (
    AkoolError,
    AkoolErrorKind,
    AkoolHttpRequest,
    AkoolHttpResponse,
)
from gateway.app.services.workers.adapters.akool import (
    AKOOL_API_KEY_REF,
    AKOOL_BASE_URL_REF,
    AKOOL_LOGICAL_TO_ENV,
    AkoolAvatarAdapter,
    AkoolFaceSwapAdapter,
    AkoolVideoGenAdapter,
    map_akool_error,
)
from gateway.app.services.workers.adapters.akool import _common as common_module

_ADAPTERS = [
    (AkoolVideoGenAdapter, VideoGenAdapter, "video_gen"),
    (AkoolAvatarAdapter, AvatarAdapter, "avatar"),
    (AkoolFaceSwapAdapter, FaceSwapAdapter, "face_swap"),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


class _StaticResolver(SecretResolver):
    def __init__(self, values: Mapping[str, Optional[str]]) -> None:
        self._values = dict(values)
        self.calls: List[str] = []

    def resolve(self, ref: SecretRef) -> Optional[str]:
        self.calls.append(ref.name)
        return self._values.get(ref.name)


class _ManualToken(CancellationToken):
    def __init__(self, *, cancelled: bool = False) -> None:
        self._cancelled = cancelled

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


class _Transport:
    def __init__(self, responses: List[AkoolHttpResponse]) -> None:
        self._responses = list(responses)
        self.requests: List[AkoolHttpRequest] = []

    def __call__(self, request: AkoolHttpRequest) -> AkoolHttpResponse:
        self.requests.append(request)
        return self._responses.pop(0)


def _credentials(**values: Optional[str]) -> AdapterCredentials:
    base: Dict[str, Optional[str]] = {
        AKOOL_API_KEY_REF.name: "k",
        AKOOL_BASE_URL_REF.name: "https://example.invalid",
    }
    base.update(values)
    return AdapterCredentials(resolver=_StaticResolver(base))


def _invocation(kind: str, **overrides: Any) -> AdapterInvocation:
    payload: Dict[str, Any] = dict(
        capability_kind=kind, inputs={"image_url": "x", "prompt": "p"}
    )
    payload.update(overrides)
    return AdapterInvocation(**payload)


def _success_transport() -> _Transport:
    # read response carries every output-field name so each capability's
    # per-family field (video / video_url / url) resolves to an output.
    return _Transport(
        [
            AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "job-1", "status": 1}}),
            AkoolHttpResponse(
                200,
                {
                    "code": 1000,
                    "data": {
                        "video_status": 3,
                        "video": "https://tmp.akool/x.mp4",
                        "video_url": "https://tmp.akool/x.mp4",
                        "url": "https://tmp.akool/x.mp4",
                    },
                },
            ),
        ]
    )


# ---------------------------------------------------------------------------
# subclass shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("adapter_cls", "base_cls", "kind"), _ADAPTERS)
def test_adapter_subclass_and_kind(adapter_cls, base_cls, kind) -> None:
    assert issubclass(adapter_cls, base_cls)
    assert adapter_cls.capability_kind == kind


@pytest.mark.parametrize(("adapter_cls", "base_cls", "kind"), _ADAPTERS)
def test_no_remaining_abstract_methods(adapter_cls, base_cls, kind) -> None:
    assert set(AdapterBase.__abstractmethods__) == {"invoke"}
    assert set(adapter_cls.__abstractmethods__) == set()


@pytest.mark.parametrize(("adapter_cls", "base_cls", "kind"), _ADAPTERS)
def test_invoke_signature_matches_base(adapter_cls, base_cls, kind) -> None:
    sig = inspect.signature(adapter_cls.invoke)
    params = list(sig.parameters.values())
    assert params[0].name == "self"
    assert params[1].name == "invocation"
    assert sig.parameters["context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["context"].default is None


# ---------------------------------------------------------------------------
# B4 lifecycle + skeleton boundary
# ---------------------------------------------------------------------------


def test_construction_is_io_free_and_resolves_no_secrets() -> None:
    creds = _credentials()
    adapter = AkoolVideoGenAdapter(credentials=creds)
    assert creds.resolver.calls == []  # type: ignore[attr-defined]
    assert adapter.credentials is creds


def test_construction_rejects_non_credentials() -> None:
    with pytest.raises(TypeError):
        AkoolVideoGenAdapter(credentials="nope")  # type: ignore[arg-type]


@pytest.mark.parametrize(("adapter_cls", "base_cls", "kind"), _ADAPTERS)
def test_invoke_without_transport_is_unavailable_no_live_call(adapter_cls, base_cls, kind) -> None:
    adapter = adapter_cls(credentials=_credentials())
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(_invocation(kind))
    # NOT_WIRED maps to UNAVAILABLE: real generation is gated, no live call.
    assert exc.value.category is AdapterErrorCategory.UNAVAILABLE


def test_invoke_resolves_api_key_at_invocation_time() -> None:
    creds = _credentials()
    adapter = AkoolVideoGenAdapter(credentials=creds, transport=_success_transport())
    adapter.invoke(_invocation("video_gen"))
    assert AKOOL_API_KEY_REF.name in creds.resolver.calls  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# secret handling
# ---------------------------------------------------------------------------


def test_invoke_without_credentials_raises_auth() -> None:
    adapter = AkoolVideoGenAdapter.__new__(AkoolVideoGenAdapter)
    VideoGenAdapter.__init__(adapter, credentials=None)
    adapter._transport = None  # type: ignore[attr-defined]
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(_invocation("video_gen"))
    assert exc.value.category is AdapterErrorCategory.AUTH


def test_missing_api_key_raises_auth() -> None:
    creds = AdapterCredentials(resolver=_StaticResolver({AKOOL_API_KEY_REF.name: None}))
    adapter = AkoolVideoGenAdapter(credentials=creds, transport=_success_transport())
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(_invocation("video_gen"))
    assert exc.value.category is AdapterErrorCategory.AUTH


# ---------------------------------------------------------------------------
# invocation validation
# ---------------------------------------------------------------------------


def test_wrong_capability_kind_rejected() -> None:
    adapter = AkoolVideoGenAdapter(credentials=_credentials(), transport=_success_transport())
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(_invocation("avatar"))  # mismatched kind for a video_gen adapter
    assert exc.value.category is AdapterErrorCategory.INVALID_INVOCATION


def test_empty_inputs_rejected() -> None:
    adapter = AkoolVideoGenAdapter(credentials=_credentials(), transport=_success_transport())
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(AdapterInvocation(capability_kind="video_gen", inputs={}))
    assert exc.value.category is AdapterErrorCategory.INVALID_INVOCATION


def test_cancellation_before_invoke_raises_cancelled() -> None:
    adapter = AkoolVideoGenAdapter(credentials=_credentials(), transport=_success_transport())
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(
            _invocation("video_gen"),
            context=AdapterExecutionContext(cancellation=_ManualToken(cancelled=True)),
        )
    assert exc.value.category is AdapterErrorCategory.CANCELLED


# ---------------------------------------------------------------------------
# B3 error mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "category", "retryable"),
    [
        (AkoolErrorKind.INVALID_REQUEST, AdapterErrorCategory.INVALID_INVOCATION, False),
        (AkoolErrorKind.NOT_FOUND, AdapterErrorCategory.INVALID_INVOCATION, False),
        (AkoolErrorKind.AUTH, AdapterErrorCategory.AUTH, False),
        (AkoolErrorKind.RATE_LIMITED, AdapterErrorCategory.RATE_LIMITED, True),
        (AkoolErrorKind.QUOTA, AdapterErrorCategory.UNAVAILABLE, False),
        (AkoolErrorKind.TIMEOUT, AdapterErrorCategory.TIMEOUT, True),
        (AkoolErrorKind.UPSTREAM, AdapterErrorCategory.UPSTREAM, True),
        (AkoolErrorKind.PROTOCOL, AdapterErrorCategory.UPSTREAM, False),
        (AkoolErrorKind.NOT_WIRED, AdapterErrorCategory.UNAVAILABLE, False),
    ],
)
def test_map_akool_error(kind, category, retryable) -> None:
    err = map_akool_error(AkoolError(kind, f"{kind.value} broke", code=1234), source="akool.video_gen")
    assert err.category is category
    assert err.retryable is retryable
    assert err.details["provider_kind"] == kind.value


def test_quota_error_through_invoke_is_unavailable_without_credit_figure() -> None:
    transport = _Transport([AkoolHttpResponse(200, {"code": 1104, "msg": "insufficient credit balance: 0"})])
    adapter = AkoolVideoGenAdapter(credentials=_credentials(), transport=transport)
    with pytest.raises(AdapterError) as exc:
        adapter.invoke(_invocation("video_gen"))
    err = exc.value
    assert err.category is AdapterErrorCategory.UNAVAILABLE
    # credit signal stripped: no numeric provider code, no 'credit' wording,
    # no balance figure in the operator-agnostic error details.
    assert set(err.details.keys()) == {"provider_kind"}
    assert err.details["provider_kind"] == "quota"
    assert "credit" not in str(err.details).lower()
    assert "1104" not in str(err.details)


# ---------------------------------------------------------------------------
# vendor leakage guard (operator-bound AdapterResult)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("adapter_cls", "base_cls", "kind"), _ADAPTERS)
def test_success_result_is_non_deliverable_and_vendor_free(adapter_cls, base_cls, kind) -> None:
    adapter = adapter_cls(credentials=_credentials(api_key="SECRET-XYZ"), transport=_success_transport())
    result = adapter.invoke(_invocation(kind, capability_kind=kind))
    assert isinstance(result, AdapterResult)
    # explicitly non-deliverable; no final.mp4 produced
    assert result.artefacts["deliverable"] is False
    assert result.artefacts["requires_copy_into_apollo_storage"] is True
    # vendor / model / credit / secret must not appear in the operator-bound surface
    blob = (repr(result.artefacts) + repr(result.advisories)).lower()
    for token in ("akool", "vendor", "model", "credit", "secret-xyz", "x-api-key", "openapi.akool"):
        assert token not in blob, f"operator-bound result leaks '{token}'"
    # no raw provider URL surfaced
    assert "http" not in blob


# ---------------------------------------------------------------------------
# absorption boundary
# ---------------------------------------------------------------------------


def test_logical_to_env_mapping_is_canonical_only() -> None:
    assert AKOOL_LOGICAL_TO_ENV[AKOOL_API_KEY_REF.name] == "AKOOL_API_KEY"
    assert AKOOL_LOGICAL_TO_ENV[AKOOL_BASE_URL_REF.name] == "AKOOL_API_BASE_URL"


def test_common_module_does_not_read_env_or_wire_runtime() -> None:
    src = inspect.getsource(common_module)
    assert "os.getenv" not in src
    assert "os.environ" not in src
    assert "from swiftcraft" not in src
    assert "import swiftcraft" not in src
    for token in (
        "gateway.app.services.packet",
        "gateway.app.services.runtime",
        "hot_follow",
        "matrix_script",
        "task_workbench",
        "delivery",
        "webhook",
    ):
        assert token not in src, f"common module leaks into {token}"


def test_no_httpx_or_webhook_in_adapter_package() -> None:
    for mod in (
        common_module,
        inspect.getmodule(AkoolVideoGenAdapter),
        inspect.getmodule(AkoolAvatarAdapter),
        inspect.getmodule(AkoolFaceSwapAdapter),
    ):
        src = inspect.getsource(mod)
        assert "import httpx" not in src
        assert "webhook" not in src.lower()

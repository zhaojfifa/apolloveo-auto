"""W2.1 first provider absorption — Gemini ``UnderstandingAdapter`` binding tests.

Covers ``gateway/app/services/workers/adapters/gemini/understanding.py``:

- B4 lifecycle: construction is I/O-free; ``invoke`` is the first reachable
  I/O surface and the only place ``resolver.resolve(...)`` is called
- B1 credential surface: credentials flow exclusively through the injected
  ``AdapterCredentials.resolver``; no env reads here
- B2 execution context: ``AdapterExecutionContext.timeout_seconds`` /
  ``cancellation`` are honoured; retry policy is NOT executed
- B3 error envelope: every provider-typed failure is mapped onto the
  closed ``AdapterErrorCategory`` set with ``source='gemini.understanding'``
- AdapterBase shape is not modified (no new dataclass / abstract surface)
- W2.1 directive boundary: only ``UnderstandingAdapter`` is bound; no
  fallback, no second provider, no packet / runtime / Hot Follow touch
"""
from __future__ import annotations

import inspect
from typing import Any, Mapping, Optional
from unittest.mock import patch

import pytest

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterError,
    AdapterErrorCategory,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    CancellationToken,
    SecretRef,
    SecretResolver,
    UnderstandingAdapter,
)
from gateway.app.services.providers.gemini import (
    GeminiTextTranslateError,
    GeminiTextTranslateErrorKind,
    GeminiTextTranslateResult,
)
from gateway.app.services.workers.adapters.gemini import (
    GEMINI_API_KEY_REF,
    GEMINI_BASE_URL_REF,
    GEMINI_LOGICAL_TO_ENV,
    GEMINI_MODEL_REF,
    GeminiUnderstandingAdapter,
)
from gateway.app.services.workers.adapters.gemini import (
    understanding as understanding_module,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


class _StaticResolver(SecretResolver):
    def __init__(self, values: Mapping[str, Optional[str]]) -> None:
        self._values = dict(values)
        self.calls: list[str] = []

    def resolve(self, ref: SecretRef) -> Optional[str]:
        self.calls.append(ref.name)
        return self._values.get(ref.name)


class _ManualToken(CancellationToken):
    def __init__(self, *, cancelled: bool = False) -> None:
        self._cancelled = cancelled
        self.poll_count = 0

    @property
    def is_cancelled(self) -> bool:
        self.poll_count += 1
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True


def _credentials(**values: Optional[str]) -> AdapterCredentials:
    base = {
        GEMINI_API_KEY_REF.name: "k",
        GEMINI_BASE_URL_REF.name: "https://example.invalid/v1",
        GEMINI_MODEL_REF.name: "gemini-2.0-flash",
    }
    base.update(values)
    return AdapterCredentials(resolver=_StaticResolver(base))


def _invocation(**overrides: Any) -> AdapterInvocation:
    payload = dict(
        capability_kind="understanding",
        inputs={
            "segments": [
                {"index": 1, "text": "hello"},
                {"index": 2, "text": "world"},
            ]
        },
        language_hint="zh",
    )
    payload.update(overrides)
    return AdapterInvocation(**payload)


def _patch_translate(result_or_exc):
    """Patch ``GeminiTextTranslateClient.translate_segments`` on the binding."""

    def _side_effect(self, request, *, cancel_check=None, http_client_factory=None):
        if cancel_check is not None and cancel_check():
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.CANCELLED,
                "cancelled mid-flight",
            )
        if isinstance(result_or_exc, Exception):
            raise result_or_exc
        return result_or_exc

    return patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_side_effect,
    )


# ---------------------------------------------------------------------------
# subclass shape
# ---------------------------------------------------------------------------


def test_adapter_subclasses_understanding_adapter() -> None:
    assert issubclass(GeminiUnderstandingAdapter, UnderstandingAdapter)
    assert GeminiUnderstandingAdapter.capability_kind == "understanding"


def test_adapter_does_not_widen_base_abstract_surface() -> None:
    # B4 freeze: ``invoke`` is the only abstract surface on the base.
    # The Gemini binding implements it, so the concrete subclass must
    # carry no remaining abstract methods.
    from gateway.app.services.capability.adapters import AdapterBase

    assert set(AdapterBase.__abstractmethods__) == {"invoke"}
    sub_abstracts = set(GeminiUnderstandingAdapter.__abstractmethods__)
    assert sub_abstracts == set()


def test_invoke_signature_matches_base() -> None:
    sig = inspect.signature(GeminiUnderstandingAdapter.invoke)
    params = list(sig.parameters.values())
    assert params[0].name == "self"
    assert params[1].name == "invocation"
    assert "context" in sig.parameters
    assert sig.parameters["context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["context"].default is None


# ---------------------------------------------------------------------------
# B4 construction-vs-invocation lifecycle
# ---------------------------------------------------------------------------


def test_construction_is_io_free_and_does_not_resolve_secrets() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    # No resolver call at construction time.
    assert creds.resolver.calls == []  # type: ignore[attr-defined]
    assert adapter.credentials is creds


def test_construction_rejects_non_credentials() -> None:
    with pytest.raises(TypeError):
        GeminiUnderstandingAdapter(credentials="nope")  # type: ignore[arg-type]


def test_invoke_resolves_credentials_at_invocation_time() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    result = GeminiTextTranslateResult(
        translated={1: "你好", 2: "世界"}, missing_indexes=(), json_repair_used=False
    )
    with _patch_translate(result):
        adapter.invoke(_invocation())
    # All three logical refs must be resolved exactly once at invoke time.
    assert sorted(creds.resolver.calls) == sorted(  # type: ignore[attr-defined]
        [
            GEMINI_API_KEY_REF.name,
            GEMINI_BASE_URL_REF.name,
            GEMINI_MODEL_REF.name,
        ]
    )


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_invoke_returns_translated_segments_in_order() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    result = GeminiTextTranslateResult(
        translated={1: "你好", 2: "世界"},
        missing_indexes=(),
        json_repair_used=False,
    )
    with _patch_translate(result):
        adapter_result = adapter.invoke(_invocation())
    assert isinstance(adapter_result, AdapterResult)
    assert adapter_result.artefacts["translated_segments"] == [
        {"index": 1, "text": "你好"},
        {"index": 2, "text": "世界"},
    ]
    assert adapter_result.artefacts["missing_indexes"] == []
    assert adapter_result.advisories == ()


def test_invoke_emits_advisory_on_json_repair() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    result = GeminiTextTranslateResult(
        translated={1: "x", 2: ""},
        missing_indexes=(2,),
        json_repair_used=True,
    )
    with _patch_translate(result):
        adapter_result = adapter.invoke(_invocation())
    assert adapter_result.artefacts["missing_indexes"] == [2]
    assert adapter_result.advisories and adapter_result.advisories[0]["kind"] == "json_repair_used"
    assert adapter_result.advisories[0]["source"] == "gemini.understanding"


def test_target_lang_falls_back_to_inputs_when_no_language_hint() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    captured: dict[str, Any] = {}

    def _capture(self, request, *, cancel_check=None, http_client_factory=None):
        captured["target_lang"] = request.target_lang
        return GeminiTextTranslateResult(translated={1: "x"})

    with patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_capture,
    ):
        adapter.invoke(
            AdapterInvocation(
                capability_kind="understanding",
                inputs={
                    "segments": [{"index": 1, "text": "hi"}],
                    "target_lang": "ja",
                },
            )
        )
    assert captured["target_lang"] == "ja"


# ---------------------------------------------------------------------------
# B1 credential failures
# ---------------------------------------------------------------------------


def test_invoke_without_credentials_raises_auth() -> None:
    adapter = GeminiUnderstandingAdapter.__new__(GeminiUnderstandingAdapter)
    UnderstandingAdapter.__init__(adapter, credentials=None)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(_invocation())
    assert exc_info.value.category is AdapterErrorCategory.AUTH
    assert exc_info.value.source == "gemini.understanding"


def test_missing_api_key_raises_auth() -> None:
    creds = AdapterCredentials(
        resolver=_StaticResolver({GEMINI_API_KEY_REF.name: None})
    )
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(_invocation())
    assert exc_info.value.category is AdapterErrorCategory.AUTH


def test_default_base_url_and_model_used_when_resolver_returns_none() -> None:
    creds = AdapterCredentials(
        resolver=_StaticResolver(
            {
                GEMINI_API_KEY_REF.name: "key",
                GEMINI_BASE_URL_REF.name: None,
                GEMINI_MODEL_REF.name: None,
            }
        )
    )
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    seen_config: dict[str, Any] = {}

    def _capture(self, request, *, cancel_check=None, http_client_factory=None):
        seen_config["base_url"] = self.config.base_url
        seen_config["model"] = self.config.model
        return GeminiTextTranslateResult(translated={1: "ok"})

    with patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_capture,
    ):
        adapter.invoke(_invocation())
    assert seen_config["base_url"].startswith("https://")
    assert seen_config["model"]


# ---------------------------------------------------------------------------
# B2 execution context: timeout / cancellation honoured (no retry execution)
# ---------------------------------------------------------------------------


def test_timeout_seconds_flows_into_provider_config() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    seen: dict[str, Any] = {}

    def _capture(self, request, *, cancel_check=None, http_client_factory=None):
        seen["timeout"] = self.config.timeout_seconds
        return GeminiTextTranslateResult(translated={1: "ok"})

    with patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_capture,
    ):
        adapter.invoke(
            _invocation(),
            context=AdapterExecutionContext(timeout_seconds=12.5),
        )
    assert seen["timeout"] == 12.5


def test_cancellation_before_invoke_raises_cancelled() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    token = _ManualToken(cancelled=True)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(
            _invocation(),
            context=AdapterExecutionContext(cancellation=token),
        )
    assert exc_info.value.category is AdapterErrorCategory.CANCELLED


def test_cancel_check_propagates_into_provider_call() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    token = _ManualToken(cancelled=False)

    def _trigger_cancel(self, request, *, cancel_check=None, http_client_factory=None):
        token.cancel()
        if cancel_check and cancel_check():
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.CANCELLED, "cancelled in flight"
            )
        return GeminiTextTranslateResult(translated={1: "ok"})

    with patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_trigger_cancel,
    ):
        with pytest.raises(AdapterError) as exc_info:
            adapter.invoke(
                _invocation(),
                context=AdapterExecutionContext(cancellation=token),
            )
    assert exc_info.value.category is AdapterErrorCategory.CANCELLED


def test_retry_policy_is_not_executed_by_adapter() -> None:
    """B2 boundary: retry-loop execution is not the adapter's job."""
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    call_count = {"n": 0}

    def _always_fail(self, request, *, cancel_check=None, http_client_factory=None):
        call_count["n"] += 1
        raise GeminiTextTranslateError(
            GeminiTextTranslateErrorKind.UPSTREAM, "upstream broke"
        )

    with patch(
        "gateway.app.services.workers.adapters.gemini.understanding."
        "GeminiTextTranslateClient.translate_segments",
        autospec=True,
        side_effect=_always_fail,
    ):
        with pytest.raises(AdapterError):
            from gateway.app.services.capability.adapters import RetryPolicy

            adapter.invoke(
                _invocation(),
                context=AdapterExecutionContext(
                    retry=RetryPolicy(max_attempts=5, initial_backoff_seconds=0.0)
                ),
            )
    # Adapter must NOT itself loop the retry policy.
    assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# B3 error envelope mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "category", "retryable"),
    [
        (GeminiTextTranslateErrorKind.INVALID_REQUEST, AdapterErrorCategory.INVALID_INVOCATION, False),
        (GeminiTextTranslateErrorKind.AUTH, AdapterErrorCategory.AUTH, False),
        (GeminiTextTranslateErrorKind.RATE_LIMITED, AdapterErrorCategory.RATE_LIMITED, True),
        (GeminiTextTranslateErrorKind.TIMEOUT, AdapterErrorCategory.TIMEOUT, True),
        (GeminiTextTranslateErrorKind.CANCELLED, AdapterErrorCategory.CANCELLED, False),
        (GeminiTextTranslateErrorKind.UPSTREAM, AdapterErrorCategory.UPSTREAM, True),
        (GeminiTextTranslateErrorKind.PROTOCOL, AdapterErrorCategory.UPSTREAM, False),
    ],
)
def test_provider_errors_map_to_closed_adapter_categories(
    kind: GeminiTextTranslateErrorKind,
    category: AdapterErrorCategory,
    retryable: bool,
) -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    exc = GeminiTextTranslateError(kind, f"{kind.value} broke", status=500)

    with _patch_translate(exc):
        with pytest.raises(AdapterError) as exc_info:
            adapter.invoke(_invocation())
    err = exc_info.value
    assert err.category is category
    assert err.source == "gemini.understanding"
    assert err.retryable is retryable
    assert err.details["provider_kind"] == kind.value


# ---------------------------------------------------------------------------
# invocation validation
# ---------------------------------------------------------------------------


def test_invocation_with_wrong_capability_kind_is_rejected() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(
            AdapterInvocation(
                capability_kind="subtitles",
                inputs={"segments": [{"index": 1, "text": "x"}]},
                language_hint="zh",
            )
        )
    assert exc_info.value.category is AdapterErrorCategory.INVALID_INVOCATION


def test_invocation_missing_segments_is_rejected() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(
            AdapterInvocation(
                capability_kind="understanding",
                inputs={"segments": []},
                language_hint="zh",
            )
        )
    assert exc_info.value.category is AdapterErrorCategory.INVALID_INVOCATION


def test_invocation_missing_target_lang_is_rejected() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(
            AdapterInvocation(
                capability_kind="understanding",
                inputs={"segments": [{"index": 1, "text": "hi"}]},
            )
        )
    assert exc_info.value.category is AdapterErrorCategory.INVALID_INVOCATION


def test_invocation_segment_missing_keys_is_rejected() -> None:
    creds = _credentials()
    adapter = GeminiUnderstandingAdapter(credentials=creds)
    with pytest.raises(AdapterError) as exc_info:
        adapter.invoke(
            AdapterInvocation(
                capability_kind="understanding",
                inputs={"segments": [{"text": "hi"}]},
                language_hint="zh",
            )
        )
    assert exc_info.value.category is AdapterErrorCategory.INVALID_INVOCATION


# ---------------------------------------------------------------------------
# absorption boundary
# ---------------------------------------------------------------------------


def test_logical_to_env_mapping_is_canonical_only() -> None:
    # Per ops/env/secret_loading_baseline_v1.md §3.1: no alias chain.
    assert GEMINI_LOGICAL_TO_ENV[GEMINI_API_KEY_REF.name] == "GEMINI_API_KEY"
    assert "GOOGLE_API_KEY" not in GEMINI_LOGICAL_TO_ENV.values()


def test_binding_module_does_not_import_packet_or_runtime_truth() -> None:
    src = inspect.getsource(understanding_module)
    assert "swiftcraft" not in src.lower()
    # No reach into packet / runtime / Hot Follow / workbench surfaces.
    forbidden = (
        "gateway.app.services.packet",
        "gateway.app.services.runtime",
        "hot_follow",
        "workbench",
    )
    for token in forbidden:
        assert token not in src, f"binding leaks into {token}"


def test_binding_module_does_not_read_env_directly() -> None:
    src = inspect.getsource(understanding_module)
    assert "os.getenv" not in src
    assert "os.environ" not in src


def test_binding_only_targets_understanding_capability() -> None:
    # Sanity guard: this PR must not slip a second adapter binding into
    # the same module. Inspect the AST class-definition surface rather
    # than the module text (the docstring intentionally enumerates the
    # capability names this PR is NOT touching).
    import ast

    tree = ast.parse(inspect.getsource(understanding_module))
    classdefs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert [c.name for c in classdefs] == ["GeminiUnderstandingAdapter"]
    base_names: list[str] = []
    for cls in classdefs:
        for base in cls.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)
    forbidden_bases = {
        "SubtitlesAdapter",
        "DubAdapter",
        "AvatarAdapter",
        "VideoGenAdapter",
        "FaceSwapAdapter",
        "PostProductionAdapter",
        "PackAdapter",
    }
    assert not (set(base_names) & forbidden_bases)

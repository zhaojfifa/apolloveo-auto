"""Gemini ↔ ``UnderstandingAdapter`` binding (W2.1 first provider absorption).

Bridges the provider-typed Gemini text-translate client (under
``gateway/app/services/providers/gemini/``) into the provider-agnostic
``UnderstandingAdapter`` surface defined in
``gateway/app/services/capability/adapters/base.py``.

Lifecycle (B4):
- Construction (``__init__``) only stores the injected ``AdapterCredentials``
  envelope and validates dependency shapes. No env reads, no network, no
  provider client construction at ``__init__``.
- ``invoke`` is the first reachable I/O point. It resolves credentials via
  ``self.credentials.resolver.resolve(...)``, constructs the provider
  client, honors the injected ``AdapterExecutionContext`` (timeout +
  cancellation token), executes the translate call, and maps any
  provider-typed failure into ``AdapterError`` with a closed
  ``AdapterErrorCategory``.

What this binding does NOT do (intentional, per W2.1 directive):
- Does NOT change ``AdapterBase`` shape.
- Does NOT register a fallback / second provider.
- Does NOT modify packet / runtime / Hot Follow code paths.
- Does NOT execute the donor's concise / strong / per-segment retry
  cascade — that is business-layer policy.
- Does NOT bind ``SubtitlesAdapter`` / ``DubAdapter`` / etc.
- Does NOT inspect or honour ``AdapterExecutionContext.retry`` itself.
  Retry-loop execution remains the (future) caller / runtime layer's
  responsibility per B2 boundary; this adapter only consumes the
  ``timeout`` and ``cancellation`` advisories that map onto a single
  provider call.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterError,
    AdapterErrorCategory,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    SecretRef,
    UnderstandingAdapter,
)
from gateway.app.services.providers.gemini import (
    GeminiTextTranslateClient,
    GeminiTextTranslateConfig,
    GeminiTextTranslateError,
    GeminiTextTranslateErrorKind,
    GeminiTextTranslateRequest,
    GeminiTextTranslateSegment,
)


# Logical secret references the binding will resolve at invoke time.
# Logical names are adapter-defined; env names are owned by
# ``ops/env/env_matrix_v1.md``. The ``EnvSecretResolver`` shim in
# ``gateway/app/services/workers/secrets/`` is the canonical way to map
# these logical names to env vars.
GEMINI_API_KEY_REF = SecretRef(
    name="gemini.translate.api_key", purpose="gemini text translate api key"
)
GEMINI_BASE_URL_REF = SecretRef(
    name="gemini.translate.base_url",
    purpose="gemini openai-compat base url",
)
GEMINI_MODEL_REF = SecretRef(
    name="gemini.translate.model", purpose="gemini text translate model id"
)

# Recommended logical→env mapping for callers wiring an ``EnvSecretResolver``.
# Reads canonical env names only per
# ``ops/env/secret_loading_baseline_v1.md`` §3.1 (no alias chain, e.g.
# ``GOOGLE_API_KEY`` is intentionally NOT included).
GEMINI_LOGICAL_TO_ENV: Mapping[str, str] = {
    GEMINI_API_KEY_REF.name: "GEMINI_API_KEY",
    GEMINI_BASE_URL_REF.name: "GEMINI_BASE_URL",
    GEMINI_MODEL_REF.name: "GEMINI_MODEL",
}

# Defaults for non-secret tuning knobs only (matches ``env_matrix_v1.md``
# §2.4 defaults). NEVER applied to ``api_key``.
_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "gemini-2.0-flash"
_DEFAULT_TIMEOUT_SECONDS = 45.0


class GeminiUnderstandingAdapter(UnderstandingAdapter):
    """``UnderstandingAdapter`` bound to the Gemini text-translate client."""

    def __init__(self, *, credentials: AdapterCredentials) -> None:
        if not isinstance(credentials, AdapterCredentials):
            raise TypeError(
                "credentials must be an AdapterCredentials instance"
            )
        super().__init__(credentials=credentials)

    def invoke(
        self,
        invocation: AdapterInvocation,
        *,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        if not isinstance(invocation, AdapterInvocation):
            raise TypeError("invocation must be an AdapterInvocation")
        if (
            context is not None
            and not isinstance(context, AdapterExecutionContext)
        ):
            raise TypeError(
                "context must be an AdapterExecutionContext when set"
            )
        if invocation.capability_kind != self.capability_kind:
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                f"capability_kind '{invocation.capability_kind}' does not "
                f"match adapter '{self.capability_kind}'",
                source="gemini.understanding",
            )

        if context is not None and context.cancellation is not None:
            context.cancellation.raise_if_cancelled()

        segments, target_lang = _extract_request(invocation)
        config = self._resolve_config(context)
        client = GeminiTextTranslateClient(config)

        cancel_check = None
        if context is not None and context.cancellation is not None:
            cancel_check = lambda: context.cancellation.is_cancelled  # noqa: E731

        request = GeminiTextTranslateRequest(
            segments=tuple(
                GeminiTextTranslateSegment(index=int(s["index"]), text=str(s["text"] or ""))
                for s in segments
            ),
            target_lang=target_lang,
        )

        try:
            result = client.translate_segments(
                request, cancel_check=cancel_check
            )
        except GeminiTextTranslateError as exc:
            raise _map_provider_error(exc) from exc

        translated_segments = [
            {
                "index": s["index"],
                "text": result.translated.get(int(s["index"]), ""),
            }
            for s in segments
        ]
        artefacts = {
            "translated_segments": translated_segments,
            "missing_indexes": list(result.missing_indexes),
        }
        advisories: tuple = ()
        if result.json_repair_used:
            advisories = (
                {
                    "kind": "json_repair_used",
                    "source": "gemini.understanding",
                },
            )
        return AdapterResult(artefacts=artefacts, advisories=advisories)

    def _resolve_config(
        self, context: Optional[AdapterExecutionContext]
    ) -> GeminiTextTranslateConfig:
        creds = self.credentials
        if creds is None:
            raise AdapterError(
                AdapterErrorCategory.AUTH,
                "gemini understanding adapter invoked without credentials",
                source="gemini.understanding",
            )
        api_key = creds.resolver.resolve(GEMINI_API_KEY_REF)
        if not api_key:
            raise AdapterError(
                AdapterErrorCategory.AUTH,
                "gemini api key is not available (logical ref "
                f"'{GEMINI_API_KEY_REF.name}')",
                source="gemini.understanding",
            )
        base_url = creds.resolver.resolve(GEMINI_BASE_URL_REF) or _DEFAULT_BASE_URL
        model = creds.resolver.resolve(GEMINI_MODEL_REF) or _DEFAULT_MODEL
        timeout_seconds = _DEFAULT_TIMEOUT_SECONDS
        if (
            context is not None
            and context.timeout_seconds is not None
        ):
            timeout_seconds = float(context.timeout_seconds)
        return GeminiTextTranslateConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )


def _extract_request(
    invocation: AdapterInvocation,
) -> tuple[list[Mapping[str, Any]], str]:
    inputs = invocation.inputs or {}
    segments_raw = inputs.get("segments")
    if not isinstance(segments_raw, list) or not segments_raw:
        raise AdapterError(
            AdapterErrorCategory.INVALID_INVOCATION,
            "invocation.inputs.segments must be a non-empty list",
            source="gemini.understanding",
        )
    segments: list[Mapping[str, Any]] = []
    for seg in segments_raw:
        if not isinstance(seg, Mapping):
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                "each segment must be a mapping with 'index' and 'text'",
                source="gemini.understanding",
            )
        if "index" not in seg or "text" not in seg:
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                "each segment must include 'index' and 'text'",
                source="gemini.understanding",
            )
        try:
            int(seg["index"])
        except (TypeError, ValueError) as exc:
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                "segment 'index' must be coercible to int",
                source="gemini.understanding",
            ) from exc
        segments.append(seg)
    target_lang = invocation.language_hint or (
        inputs.get("target_lang") if isinstance(inputs, Mapping) else None
    )
    if not isinstance(target_lang, str) or not target_lang:
        raise AdapterError(
            AdapterErrorCategory.INVALID_INVOCATION,
            "target language must be supplied via "
            "invocation.language_hint or invocation.inputs.target_lang",
            source="gemini.understanding",
        )
    return segments, target_lang


_PROVIDER_KIND_TO_CATEGORY = {
    GeminiTextTranslateErrorKind.INVALID_REQUEST: AdapterErrorCategory.INVALID_INVOCATION,
    GeminiTextTranslateErrorKind.AUTH: AdapterErrorCategory.AUTH,
    GeminiTextTranslateErrorKind.RATE_LIMITED: AdapterErrorCategory.RATE_LIMITED,
    GeminiTextTranslateErrorKind.TIMEOUT: AdapterErrorCategory.TIMEOUT,
    GeminiTextTranslateErrorKind.CANCELLED: AdapterErrorCategory.CANCELLED,
    GeminiTextTranslateErrorKind.UPSTREAM: AdapterErrorCategory.UPSTREAM,
    GeminiTextTranslateErrorKind.PROTOCOL: AdapterErrorCategory.UPSTREAM,
}

_RETRYABLE_KINDS = frozenset(
    {
        GeminiTextTranslateErrorKind.RATE_LIMITED,
        GeminiTextTranslateErrorKind.TIMEOUT,
        GeminiTextTranslateErrorKind.UPSTREAM,
    }
)


def _map_provider_error(exc: GeminiTextTranslateError) -> AdapterError:
    category = _PROVIDER_KIND_TO_CATEGORY.get(
        exc.kind, AdapterErrorCategory.UPSTREAM
    )
    details: dict[str, Any] = {"provider_kind": exc.kind.value}
    if exc.status is not None:
        details["status"] = exc.status
    return AdapterError(
        category,
        str(exc),
        source="gemini.understanding",
        retryable=(exc.kind in _RETRYABLE_KINDS),
        details=details,
    )

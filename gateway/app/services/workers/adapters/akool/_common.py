"""Shared Akool adapter skeleton machinery (PR-1).

Holds the provider-agnostic glue every Akool capability adapter needs:
secret refs, logical→env mapping, ``AkoolError`` → ``AdapterError`` mapping,
invocation-time config resolution, and a single shared invoke body that is a
*skeleton* (no live call, no polling loop, no media assembly, no provider URL
as deliverable).

Boundary (PR-1 approval): everything here maps/validates/sanitises only. Real
generation is gated behind Capability Expansion W2.3 — with no injected
transport the underlying client raises ``NOT_WIRED`` and this layer maps it to
``AdapterError(UNAVAILABLE)``.
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
)
from gateway.app.services.providers.akool import (
    AkoolCapability,
    AkoolClient,
    AkoolClientConfig,
    AkoolError,
    AkoolErrorKind,
    AkoolTaskStatus,
    AkoolTransport,
)

# Logical secret references resolved at invoke time. Logical names are
# adapter-defined; env names are owned by ``ops/env/env_matrix_v1.md``.
AKOOL_API_KEY_REF = SecretRef(name="akool.api_key", purpose="akool openapi api key")
AKOOL_BASE_URL_REF = SecretRef(name="akool.base_url", purpose="akool openapi base url")

# Canonical logical→env mapping (no alias chain).
AKOOL_LOGICAL_TO_ENV: Mapping[str, str] = {
    AKOOL_API_KEY_REF.name: "AKOOL_API_KEY",
    AKOOL_BASE_URL_REF.name: "AKOOL_API_BASE_URL",
}

# Closed provider-kind → provider-agnostic category mapping. Credits / quota
# are mapped to UNAVAILABLE (operator-safe); the credit signal itself is never
# surfaced. ``NOT_WIRED`` (the skeleton sentinel) also maps to UNAVAILABLE.
_PROVIDER_KIND_TO_CATEGORY: Mapping[AkoolErrorKind, AdapterErrorCategory] = {
    AkoolErrorKind.INVALID_REQUEST: AdapterErrorCategory.INVALID_INVOCATION,
    AkoolErrorKind.NOT_FOUND: AdapterErrorCategory.INVALID_INVOCATION,
    AkoolErrorKind.AUTH: AdapterErrorCategory.AUTH,
    AkoolErrorKind.RATE_LIMITED: AdapterErrorCategory.RATE_LIMITED,
    AkoolErrorKind.QUOTA: AdapterErrorCategory.UNAVAILABLE,
    AkoolErrorKind.TIMEOUT: AdapterErrorCategory.TIMEOUT,
    AkoolErrorKind.UPSTREAM: AdapterErrorCategory.UPSTREAM,
    AkoolErrorKind.PROTOCOL: AdapterErrorCategory.UPSTREAM,
    AkoolErrorKind.NOT_WIRED: AdapterErrorCategory.UNAVAILABLE,
}

_RETRYABLE_KINDS = frozenset(
    {
        AkoolErrorKind.RATE_LIMITED,
        AkoolErrorKind.TIMEOUT,
        AkoolErrorKind.UPSTREAM,
    }
)

_DEFAULT_BASE_URL = "https://openapi.akool.com"


def map_akool_error(exc: AkoolError, *, source: str) -> AdapterError:
    """Translate a provider-typed ``AkoolError`` into ``AdapterError``.

    Vendor/model/credit specifics are NOT carried as first-class fields. Only
    the closed ``provider_kind`` is placed in ``details`` (a generic kind tag,
    never a credit figure or numeric provider code).
    """
    category = _PROVIDER_KIND_TO_CATEGORY.get(exc.kind, AdapterErrorCategory.UPSTREAM)
    return AdapterError(
        category,
        str(exc),
        source=source,
        retryable=(exc.kind in _RETRYABLE_KINDS),
        details={"provider_kind": exc.kind.value},
    )


def resolve_config(
    credentials: Optional[AdapterCredentials],
    context: Optional[AdapterExecutionContext],
    *,
    source: str,
) -> AkoolClientConfig:
    """Resolve the Akool client config at invocation time (B1/B4).

    Raises ``AdapterError(AUTH)`` when credentials or the api key are absent.
    The resolved api key is handed straight to the config and never logged or
    returned in any result/advisory.
    """
    if credentials is None:
        raise AdapterError(
            AdapterErrorCategory.AUTH,
            "akool adapter invoked without credentials",
            source=source,
        )
    api_key = credentials.resolver.resolve(AKOOL_API_KEY_REF)
    if not api_key:
        raise AdapterError(
            AdapterErrorCategory.AUTH,
            f"akool api key is not available (logical ref '{AKOOL_API_KEY_REF.name}')",
            source=source,
        )
    base_url = credentials.resolver.resolve(AKOOL_BASE_URL_REF) or _DEFAULT_BASE_URL
    timeout_seconds = 30.0
    if context is not None and context.timeout_seconds is not None:
        timeout_seconds = float(context.timeout_seconds)
    return AkoolClientConfig(
        api_key=api_key, base_url=base_url, timeout_seconds=timeout_seconds
    )


class AkoolAdapterSkeletonMixin:
    """Shared skeleton invoke body for every Akool capability adapter.

    Subclasses set ``_akool_capability`` (an ``AkoolCapability``) and
    ``_source`` (developer diagnostic tag, e.g. ``"akool.video_gen"``). The
    real Apollo capability kind is pinned by the concrete ``*Adapter`` base.

    A test/future-PR transport may be injected at construction via
    ``transport=``; PR-1 ships no default transport, so a production
    construction reaches ``NOT_WIRED`` → ``AdapterError(UNAVAILABLE)`` and
    makes no live call.
    """

    _akool_capability: AkoolCapability
    _source: str

    def __init__(
        self,
        *,
        credentials: AdapterCredentials,
        transport: Optional[AkoolTransport] = None,
    ) -> None:
        if not isinstance(credentials, AdapterCredentials):
            raise TypeError("credentials must be an AdapterCredentials instance")
        if transport is not None and not callable(transport):
            raise TypeError("transport must be callable when set")
        # AdapterBase.__init__ (via the concrete *Adapter) stores credentials.
        super().__init__(credentials=credentials)  # type: ignore[call-arg]
        self._transport = transport

    def _build_params(self, invocation: AdapterInvocation) -> Mapping[str, Any]:
        """Map a contract-shaped invocation into Akool create params.

        Skeleton: only forwards the contract-shaped ``inputs`` mapping. No
        vendor/model identifiers are injected. Capability-specific param
        shaping is deferred to a later, separately approved PR.
        """
        inputs = invocation.inputs
        if not isinstance(inputs, Mapping) or not inputs:
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                "invocation.inputs must be a non-empty mapping",
                source=self._source,
            )
        return dict(inputs)

    def _invoke_skeleton(
        self,
        invocation: AdapterInvocation,
        *,
        expected_kind: str,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        if not isinstance(invocation, AdapterInvocation):
            raise TypeError("invocation must be an AdapterInvocation")
        if context is not None and not isinstance(context, AdapterExecutionContext):
            raise TypeError("context must be an AdapterExecutionContext when set")
        if invocation.capability_kind != expected_kind:
            raise AdapterError(
                AdapterErrorCategory.INVALID_INVOCATION,
                f"capability_kind '{invocation.capability_kind}' does not match "
                f"adapter '{expected_kind}'",
                source=self._source,
            )
        if context is not None and context.cancellation is not None:
            context.cancellation.raise_if_cancelled()

        params = self._build_params(invocation)
        config = resolve_config(
            getattr(self, "credentials", None), context, source=self._source
        )
        client = AkoolClient(config, transport=self._transport)

        try:
            created = client.create_task(self._akool_capability, params)
            read = client.read_task_result(
                self._akool_capability, created.provider_task_id
            )
        except AkoolError as exc:
            raise map_akool_error(exc, source=self._source) from exc

        # Sanitised, operator-safe, explicitly non-deliverable result.
        # NOTE: no provider URL, no provider task id, no vendor/model/credit
        # token is placed in artefacts/advisories. Even on provider SUCCESS,
        # the provider output is NEVER a deliverable here — it must be copied
        # into Apollo artifact storage by a later, separately approved PR.
        produced_output = read.output is not None and not read.output.is_deliverable
        artefacts: Mapping[str, Any] = {
            "provider_attempt_status": read.status.name.lower(),
            "provider_output_present": read.output is not None,
            "deliverable": False,
            "requires_copy_into_apollo_storage": bool(produced_output),
        }
        # Advisory ``source`` is the neutral Apollo capability kind, NOT the
        # vendor diagnostic tag — ``AdapterResult`` is the operator-bound
        # surface and must carry no vendor / model / credit identifier.
        advisories = (
            {"kind": "real_generation_gated", "source": expected_kind},
            {"kind": "provider_output_not_deliverable", "source": expected_kind},
        )
        return AdapterResult(artefacts=artefacts, advisories=advisories)

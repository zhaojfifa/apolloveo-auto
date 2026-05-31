"""Akool provider client — SKELETON ONLY (PR-1, donor rows P-01 / P-02).

Authority:
- ``docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`` (PR-1 row).
- ``docs/donor/swiftcraft_capability_mapping_v1.md`` rows P-01 (Akool client
  consolidation) / P-02 (duplicate merge).
- Capability adapter base interfaces under
  ``gateway/app/services/capability/adapters/`` (the worker-side binding maps
  this provider client's typed errors into ``AdapterError``).

WHAT THIS MODULE IS (hard boundary — PR-1 approval):
- A *skeleton* provider client: request-shape construction, response parsing,
  a closed provider error taxonomy + Akool ``code`` → kind mapping, and the
  binding rule that **a provider temporary URL is NEVER a deliverable**.

WHAT THIS MODULE IS NOT (forbidden by the PR-1 review — do NOT add here):
- NO live Akool API call. This client imports no HTTP library and owns no
  socket. Every request is handed to an *injected* ``transport`` callable;
  with no transport the client raises ``AkoolError(NOT_WIRED)``. There is no
  default network path to accidentally fire.
- NO polling loop / worker runtime. ``read_task_result`` performs a single
  read; it never loops or sleeps.
- NO webhook handling. (Webhook decryption is a separate, later, approved PR.)
- NO Matrix Script / Delivery Center / packet / template wiring.
- NO ``final.mp4`` generation, assembly, or storage write.
- NO treatment of a provider URL as artifact / deliverable truth.

Lifecycle:
- Construction is I/O-free and side-effect-free (only stores config + the
  optional injected transport).
- ``create_task`` / ``read_task_result`` are the only methods that *would*
  reach a transport; they call the injected transport once and parse its
  result. No transport → ``AkoolError(NOT_WIRED)``.
- Secret values are never read from the environment here and are never logged;
  the api key arrives via config (resolved by the adapter binding's
  ``SecretResolver`` at invocation time) and is placed only on the outgoing
  request header object handed to the transport.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional

# Akool OpenAPI base; non-secret default tuning knob only.
_DEFAULT_BASE_URL = "https://openapi.akool.com"
_DEFAULT_TIMEOUT_SECONDS = 30.0

# Akool business success sentinel (lives in the JSON body ``code``; HTTP status
# is NOT the signal per the Akool API docs).
AKOOL_SUCCESS_CODE = 1000


class AkoolCapability(str, Enum):
    """Closed set of Akool capabilities this skeleton knows how to shape.

    These are *provider-internal* capability tags, not operator-visible and
    not Apollo capability kinds. The worker-side adapter binds each to the
    proper Apollo capability kind (``video_gen`` / ``avatar`` / ``face_swap``
    / ``lip_sync`` / ``dub``).
    """

    TALKING_PHOTO = "talking_photo"
    TALKING_AVATAR = "talking_avatar"
    IMAGE_TO_VIDEO = "image_to_video"
    FACE_SWAP = "face_swap"
    LIP_SYNC = "lip_sync"
    TTS = "tts"


class AkoolTaskStatus(int, Enum):
    """Uniform Akool async status enum (per Akool API docs)."""

    QUEUED = 1
    PROCESSING = 2
    SUCCESS = 3
    FAILED = 4


class AkoolErrorKind(str, Enum):
    """Closed, provider-internal failure shape.

    Mirrors the failure categories the worker-side adapter needs in order to
    map into the provider-agnostic ``AdapterErrorCategory``. Deliberately
    small; not a generic HTTP taxonomy.

    ``NOT_WIRED`` is the skeleton sentinel: it is raised when a method that
    would reach the network is called without an injected ``transport``. It
    encodes the PR-1 boundary "no live call" as a typed failure rather than a
    silent no-op.
    """

    INVALID_REQUEST = "invalid_request"
    AUTH = "auth"
    RATE_LIMITED = "rate_limited"
    QUOTA = "quota"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    UPSTREAM = "upstream"
    PROTOCOL = "protocol"
    NOT_WIRED = "not_wired"


class AkoolError(Exception):
    """Provider-typed failure raised by ``AkoolClient``.

    The worker-side adapter translates this into ``AdapterError`` so the
    provider-agnostic boundary holds at the ``AdapterBase`` surface. The
    Akool numeric ``code`` is kept on ``code`` for diagnostics only; it MUST
    NOT leak into ``AdapterError`` first-class fields, and any credit-balance
    figure MUST be stripped before any operator-bound surface.
    """

    __slots__ = ("kind", "code", "upstream_snippet")

    def __init__(
        self,
        kind: "AkoolErrorKind",
        message: str,
        *,
        code: Optional[int] = None,
        upstream_snippet: Optional[str] = None,
    ) -> None:
        if not isinstance(kind, AkoolErrorKind):
            raise TypeError("kind must be an AkoolErrorKind")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        if code is not None and (isinstance(code, bool) or not isinstance(code, int)):
            raise TypeError("code must be int when set")
        if upstream_snippet is not None and not isinstance(upstream_snippet, str):
            raise TypeError("upstream_snippet must be str when set")
        self.kind = kind
        self.code = code
        self.upstream_snippet = upstream_snippet
        super().__init__(message)


# Akool numeric ``code`` → provider error kind. Authority: Akool error-code
# reference (https://docs.akool.com/ai-tools-suite/error-code). Codes not
# listed here fall through to ``UPSTREAM`` (processing-failure ranges, etc.).
_CODE_TO_KIND: Mapping[int, AkoolErrorKind] = MappingProxyType(
    {
        1003: AkoolErrorKind.INVALID_REQUEST,  # parameter error
        1005: AkoolErrorKind.RATE_LIMITED,  # operation too frequent
        1006: AkoolErrorKind.QUOTA,  # insufficient quota balance
        1104: AkoolErrorKind.QUOTA,  # insufficient credit balance
        1103: AkoolErrorKind.QUOTA,  # not paid / overdue
        1213: AkoolErrorKind.QUOTA,  # subscription required
        1221: AkoolErrorKind.QUOTA,  # subscription required
        1008: AkoolErrorKind.NOT_FOUND,  # content not exist
        1014: AkoolErrorKind.NOT_FOUND,  # resource not exist
        1015: AkoolErrorKind.NOT_FOUND,  # resource not exist
        1009: AkoolErrorKind.AUTH,  # permission denied
        1101: AkoolErrorKind.AUTH,  # illegal / expired token
        1102: AkoolErrorKind.AUTH,  # token empty
        1109: AkoolErrorKind.AUTH,  # account not exist
        1200: AkoolErrorKind.AUTH,  # account blocked
    }
)


def classify_akool_code(code: int) -> AkoolErrorKind:
    """Map an Akool body ``code`` to a closed provider error kind.

    ``AKOOL_SUCCESS_CODE`` must never be passed here (it is not a failure).
    Unknown / processing-failure codes map to ``UPSTREAM``.
    """
    if isinstance(code, bool) or not isinstance(code, int):
        raise TypeError("code must be int")
    if code == AKOOL_SUCCESS_CODE:
        raise ValueError("classify_akool_code called with the success code")
    return _CODE_TO_KIND.get(code, AkoolErrorKind.UPSTREAM)


@dataclass(frozen=True)
class AkoolClientConfig:
    """Resolved, in-memory configuration handed to the client.

    All fields are caller-resolved (the adapter binding resolves the api key
    via ``SecretResolver`` at invocation time). The client never reads env.
    """

    api_key: str
    base_url: str = _DEFAULT_BASE_URL
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, str) or not self.api_key:
            raise ValueError("api_key must be a non-empty string")
        if not isinstance(self.base_url, str) or not self.base_url:
            raise ValueError("base_url must be a non-empty string")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a positive number")


@dataclass(frozen=True)
class AkoolHttpRequest:
    """Outgoing request descriptor handed to the injected ``transport``.

    This is what a real transport *would* send. The api key lives only here,
    on the ``x-api-key`` header, and never appears in parsed results, errors,
    advisories, or logs.
    """

    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    json_body: Optional[Mapping[str, Any]] = None
    query: Optional[Mapping[str, str]] = None


@dataclass(frozen=True)
class AkoolHttpResponse:
    """Transport response descriptor (test fakes build this directly)."""

    status_code: int
    body: Mapping[str, Any]


# A transport is any callable that turns a request descriptor into a response
# descriptor. Production wiring of a real transport is a *later, separately
# approved* PR; PR-1 ships no live transport.
AkoolTransport = Callable[[AkoolHttpRequest], AkoolHttpResponse]


@dataclass(frozen=True)
class ProviderTemporaryOutput:
    """A provider's temporary output reference — explicitly NOT a deliverable.

    Akool generated outputs are temporary URLs (valid ~7 days per the Akool
    docs). The binding rule (PR-0 design §4 / §6.2) is: **a provider URL is
    never deliverable truth**; it must be copied into Apollo artifact storage
    on completion, and only the resulting Apollo ``ArtifactHandle`` is a
    deliverable. This value object encodes that rule structurally:

    - ``is_deliverable`` is always ``False``.
    - ``requires_copy_into_apollo_storage`` is always ``True``.
    - ``as_deliverable()`` raises — there is no path that turns this into a
      deliverable inside the provider layer.
    """

    url: str
    expires_in_days_hint: int = 7

    @property
    def is_deliverable(self) -> bool:
        return False

    @property
    def requires_copy_into_apollo_storage(self) -> bool:
        return True

    def as_deliverable(self) -> Any:
        raise AkoolError(
            AkoolErrorKind.INVALID_REQUEST,
            "a provider temporary URL is never a deliverable; copy it into "
            "Apollo artifact storage and bind the resulting ArtifactHandle",
        )


@dataclass(frozen=True)
class AkoolCreateResult:
    """Parsed result of a create call: the provider task handle + status.

    ``provider_task_id`` is the Akool ``_id`` (L4-only; never operator-visible).
    """

    provider_task_id: str
    status: AkoolTaskStatus


@dataclass(frozen=True)
class AkoolTaskResult:
    """Parsed result of a single (non-looping) result read.

    ``output`` is populated only on ``SUCCESS`` and is always a
    ``ProviderTemporaryOutput`` — never a bare deliverable URL.
    """

    provider_task_id: str
    status: AkoolTaskStatus
    output: Optional[ProviderTemporaryOutput] = None


# Per-capability create endpoints + the body field carrying the provider task
# id, and the result endpoint + status/output fields. Lifted from the Akool
# API docs; exact field casing must be re-locked against ``openapi.json``
# before any real transport is wired (PR-0 §4 note).
_CREATE_PATHS: Mapping[AkoolCapability, str] = MappingProxyType(
    {
        AkoolCapability.TALKING_PHOTO: "/api/open/v3/content/video/createbytalkingphoto",
        AkoolCapability.TALKING_AVATAR: "/api/open/v3/talkingavatar/create",
        AkoolCapability.IMAGE_TO_VIDEO: "/api/open/v4/image2Video/createBySourcePrompt",
        AkoolCapability.FACE_SWAP: "/api/open/v4/faceswap/faceswapPlusByImage",
        AkoolCapability.LIP_SYNC: "/api/open/v3/content/video/lipsync",
        AkoolCapability.TTS: "/api/open/v4/voice/tts",
    }
)

# Output URL field name per result family (video / faceswap / image2video / tts).
_OUTPUT_FIELDS: Mapping[AkoolCapability, str] = MappingProxyType(
    {
        AkoolCapability.TALKING_PHOTO: "video",
        AkoolCapability.TALKING_AVATAR: "video",
        AkoolCapability.IMAGE_TO_VIDEO: "video_url",
        AkoolCapability.FACE_SWAP: "url",
        AkoolCapability.LIP_SYNC: "video",
        AkoolCapability.TTS: "preview",
    }
)


class AkoolClient:
    """Minimal, transport-injected Akool client. No live I/O of its own.

    Construction is pure. The only methods that reach a transport
    (``create_task`` / ``read_task_result``) call the *injected* transport
    exactly once; with no transport they raise ``AkoolError(NOT_WIRED)``.
    """

    def __init__(
        self,
        config: AkoolClientConfig,
        *,
        transport: Optional[AkoolTransport] = None,
    ) -> None:
        if not isinstance(config, AkoolClientConfig):
            raise TypeError("config must be an AkoolClientConfig")
        if transport is not None and not callable(transport):
            raise TypeError("transport must be callable when set")
        self._config = config
        self._transport = transport

    @property
    def config(self) -> AkoolClientConfig:
        return self._config

    @property
    def is_wired(self) -> bool:
        """``True`` only if a transport has been injected (tests / future PR)."""
        return self._transport is not None

    def _headers(self) -> Mapping[str, str]:
        # The api key lives ONLY here, on the outgoing header. Never logged,
        # never returned in results/errors.
        return {
            "x-api-key": self._config.api_key,
            "Content-Type": "application/json",
        }

    def _send(self, request: AkoolHttpRequest) -> AkoolHttpResponse:
        if self._transport is None:
            raise AkoolError(
                AkoolErrorKind.NOT_WIRED,
                "akool client is a skeleton: no live transport is wired; real "
                "generation is gated behind Capability Expansion W2.3",
            )
        response = self._transport(request)
        if not isinstance(response, AkoolHttpResponse):
            raise AkoolError(
                AkoolErrorKind.PROTOCOL,
                "transport did not return an AkoolHttpResponse",
            )
        return response

    @staticmethod
    def _raise_for_body_code(body: Mapping[str, Any]) -> None:
        if not isinstance(body, Mapping):
            raise AkoolError(
                AkoolErrorKind.PROTOCOL, "akool response body was not a mapping"
            )
        code = body.get("code")
        if code == AKOOL_SUCCESS_CODE:
            return
        if isinstance(code, bool) or not isinstance(code, int):
            raise AkoolError(
                AkoolErrorKind.PROTOCOL,
                "akool response body missing integer 'code'",
            )
        kind = classify_akool_code(code)
        # NOTE: deliberately do not echo provider 'msg' verbatim or any credit
        # figure; the developer diagnostic names only the closed kind + code.
        raise AkoolError(
            kind,
            f"akool rejected request (kind={kind.value})",
            code=code,
        )

    def create_task(
        self,
        capability: AkoolCapability,
        params: Mapping[str, Any],
    ) -> AkoolCreateResult:
        """Build + send a single create request; parse the task handle.

        Does NOT poll. Does NOT assemble media. With no transport this raises
        ``AkoolError(NOT_WIRED)`` before any network would occur.
        """
        if not isinstance(capability, AkoolCapability):
            raise TypeError("capability must be an AkoolCapability")
        if not isinstance(params, Mapping):
            raise TypeError("params must be a mapping")
        path = _CREATE_PATHS[capability]
        request = AkoolHttpRequest(
            method="POST",
            url=f"{self._config.base_url.rstrip('/')}{path}",
            headers=self._headers(),
            json_body=dict(params),
        )
        response = self._send(request)
        self._raise_for_body_code(response.body)
        data = response.body.get("data")
        if not isinstance(data, Mapping):
            raise AkoolError(
                AkoolErrorKind.PROTOCOL, "akool create response missing 'data'"
            )
        provider_task_id = data.get("_id") or data.get("task_id") or data.get("job_id")
        if not isinstance(provider_task_id, str) or not provider_task_id:
            raise AkoolError(
                AkoolErrorKind.PROTOCOL,
                "akool create response missing provider task id",
            )
        status = _parse_status(data)
        return AkoolCreateResult(provider_task_id=provider_task_id, status=status)

    def read_task_result(
        self,
        capability: AkoolCapability,
        provider_task_id: str,
    ) -> AkoolTaskResult:
        """Single, non-looping result read for a provider task.

        This is NOT a polling worker: it performs exactly one transport call
        and returns the current status. Any orchestration / retry / wait is a
        later, separately approved concern (and is forbidden in PR-1).
        """
        if not isinstance(capability, AkoolCapability):
            raise TypeError("capability must be an AkoolCapability")
        if not isinstance(provider_task_id, str) or not provider_task_id:
            raise ValueError("provider_task_id must be a non-empty string")
        request = AkoolHttpRequest(
            method="GET",
            url=f"{self._config.base_url.rstrip('/')}/api/open/v3/content/video/infobymodelid",
            headers=self._headers(),
            query={"video_model_id": provider_task_id},
        )
        response = self._send(request)
        self._raise_for_body_code(response.body)
        data = response.body.get("data")
        if not isinstance(data, Mapping):
            raise AkoolError(
                AkoolErrorKind.PROTOCOL, "akool result response missing 'data'"
            )
        status = _parse_status(data)
        output: Optional[ProviderTemporaryOutput] = None
        if status is AkoolTaskStatus.SUCCESS:
            url = data.get(_OUTPUT_FIELDS[capability])
            if isinstance(url, str) and url:
                # Wrapped — never a bare deliverable URL.
                output = ProviderTemporaryOutput(url=url)
        return AkoolTaskResult(
            provider_task_id=provider_task_id, status=status, output=output
        )


def _parse_status(data: Mapping[str, Any]) -> AkoolTaskStatus:
    """Normalise the three Akool status field names into one enum.

    Video family uses ``video_status``; faceswap uses ``faceswap_status``;
    image2video / tts use ``status``.
    """
    raw = (
        data.get("video_status")
        if "video_status" in data
        else data.get("faceswap_status")
        if "faceswap_status" in data
        else data.get("status")
    )
    try:
        return AkoolTaskStatus(int(raw))
    except (TypeError, ValueError) as exc:
        raise AkoolError(
            AkoolErrorKind.PROTOCOL,
            "akool response carried an unrecognised status value",
        ) from exc

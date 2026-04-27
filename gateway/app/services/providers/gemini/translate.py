"""Gemini text-translation provider client (W2.1 A-03 absorption).

Donor: ``backend/app/utils/translate_gemini.py`` (W2.1 wave pin per
``docs/donor/swiftcraft_capability_mapping_v1.md`` row A-03).

Scope frozen for the W2.1 first provider absorption wave:

- Single capability: text translation of a list of indexed segments via the
  OpenAI-compatible ``/chat/completions`` endpoint exposed by Gemini.
- Provider client carries NO credential discovery, NO env reads, and NO
  business fallback / retry / concise-rewrite orchestration. The donor's
  multi-stage retry / concise / strong-retry / per-segment retry / raw-save
  strategy is intentionally NOT absorbed in this PR — it is business-layer
  fallback policy and belongs to a later wave (and to whatever
  ``UnderstandingAdapter`` caller chooses to run it).
- Construction is pure: only assigns config + builds an ``httpx.Timeout``.
  No network, no disk, no env access, no logger binding at construction.
- Network access happens only when ``translate_segments`` is called. Errors
  are raised as a single provider-typed exception (``GeminiTextTranslateError``)
  carrying a closed ``GeminiTextTranslateErrorKind``; the worker-side
  ``UnderstandingAdapter`` binding maps these into ``AdapterError``.
- Cancellation is honored cooperatively via an injected
  ``cancel_check: Callable[[], bool] | None``. Timeout is enforced via the
  per-request ``httpx.Timeout`` derived from the injected
  ``timeout_seconds``.

What this module does NOT do (intentional, per W2.1 directive):

- Does NOT read ``GEMINI_API_KEY`` / ``GEMINI_BASE_URL`` / ``GEMINI_MODEL``
  from the process environment. Resolution belongs to ``SecretResolver``
  (B1) at the adapter binding layer.
- Does NOT raise ``AdapterError`` directly. Mapping into the
  provider-agnostic ``AdapterError`` envelope (B3) is the adapter
  binding's job, so the provider client stays usable in isolation and the
  AdapterBase shape is not touched.
- Does NOT wire into runtime / router / packet / Hot Follow code paths.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Optional, Sequence

import httpx


class GeminiTextTranslateErrorKind(str, Enum):
    """Closed, provider-internal failure shape.

    Mirrors the failure categories the worker-side adapter binding needs in
    order to map into the provider-agnostic ``AdapterErrorCategory``. Kept
    deliberately small — this is not a generic HTTP error taxonomy.
    """

    INVALID_REQUEST = "invalid_request"
    AUTH = "auth"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UPSTREAM = "upstream"
    PROTOCOL = "protocol"


class GeminiTextTranslateError(Exception):
    """Provider-typed failure raised by ``GeminiTextTranslateClient``.

    The adapter binding translates this into ``AdapterError`` so the
    provider-agnostic boundary is preserved at the AdapterBase surface.
    Provider-specific HTTP status codes and upstream messages are kept on
    ``status`` / ``upstream_snippet`` for diagnostic use only — they MUST
    NOT leak into ``AdapterError`` first-class fields.
    """

    __slots__ = ("kind", "status", "upstream_snippet")

    def __init__(
        self,
        kind: GeminiTextTranslateErrorKind,
        message: str,
        *,
        status: Optional[int] = None,
        upstream_snippet: Optional[str] = None,
    ) -> None:
        if not isinstance(kind, GeminiTextTranslateErrorKind):
            raise TypeError("kind must be a GeminiTextTranslateErrorKind")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        if status is not None and not isinstance(status, int):
            raise TypeError("status must be int when set")
        if upstream_snippet is not None and not isinstance(
            upstream_snippet, str
        ):
            raise TypeError("upstream_snippet must be str when set")
        self.kind = kind
        self.status = status
        self.upstream_snippet = upstream_snippet
        super().__init__(message)


@dataclass(frozen=True)
class GeminiTextTranslateConfig:
    """Resolved, in-memory configuration handed to the client.

    All fields are caller-resolved (e.g. via ``SecretResolver`` at the
    adapter binding layer). The provider client never reads env directly.
    """

    api_key: str
    base_url: str
    model: str = "gemini-2.0-flash"
    timeout_seconds: float = 45.0
    connect_timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, str) or not self.api_key:
            raise ValueError("api_key must be a non-empty string")
        if not isinstance(self.base_url, str) or not self.base_url:
            raise ValueError("base_url must be a non-empty string")
        if not isinstance(self.model, str) or not self.model:
            raise ValueError("model must be a non-empty string")
        for fname in ("timeout_seconds", "connect_timeout_seconds"):
            value = getattr(self, fname)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                raise ValueError(f"{fname} must be a positive number")


@dataclass(frozen=True)
class GeminiTextTranslateSegment:
    """Single segment in a translation request."""

    index: int
    text: str

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError("index must be int")
        if not isinstance(self.text, str):
            raise TypeError("text must be str")


@dataclass(frozen=True)
class GeminiTextTranslateRequest:
    """Translation request: indexed segments + target language."""

    segments: Sequence[GeminiTextTranslateSegment]
    target_lang: str

    def __post_init__(self) -> None:
        if not isinstance(self.target_lang, str) or not self.target_lang:
            raise ValueError("target_lang must be a non-empty string")
        if not isinstance(self.segments, Sequence) or isinstance(
            self.segments, (str, bytes)
        ):
            raise TypeError("segments must be a sequence")
        for s in self.segments:
            if not isinstance(s, GeminiTextTranslateSegment):
                raise TypeError(
                    "segments must contain GeminiTextTranslateSegment"
                )


@dataclass(frozen=True)
class GeminiTextTranslateResult:
    """Translation result: per-index translated text + missing indexes.

    No business truth keys (no `translation_dubbing_final` /
    `translation_subtitle_final` fan-out — that was the donor's
    business-layer concern, not ours).
    """

    translated: Mapping[int, str]
    missing_indexes: tuple = ()
    json_repair_used: bool = False


_PROMPT_HEADER = (
    "Translate the input subtitles to the target language.\n"
    "Rules: one segment in, one segment out; keep the same index; "
    "natural spoken phrasing fit for dubbing; concise; no explanation; "
    "no added detail.\n"
    "Output strict JSON only.\n"
    'Return exactly: {"segments":[{"index":1,"text":"..."}, ...]}\n'
)


class GeminiTextTranslateClient:
    """Minimal, side-effect-free Gemini text-translation client.

    Construction is I/O-free. Network access happens only inside
    ``translate_segments``.
    """

    def __init__(self, config: GeminiTextTranslateConfig) -> None:
        if not isinstance(config, GeminiTextTranslateConfig):
            raise TypeError("config must be a GeminiTextTranslateConfig")
        self._config = config
        self._timeout = httpx.Timeout(
            config.timeout_seconds, connect=config.connect_timeout_seconds
        )

    @property
    def config(self) -> GeminiTextTranslateConfig:
        return self._config

    def translate_segments(
        self,
        request: GeminiTextTranslateRequest,
        *,
        cancel_check: Optional[Callable[[], bool]] = None,
        http_client_factory: Optional[
            Callable[[httpx.Timeout], httpx.Client]
        ] = None,
    ) -> GeminiTextTranslateResult:
        """Translate ``request`` and return per-index translated text.

        ``cancel_check`` is polled before the network call; if it returns
        ``True`` a ``CANCELLED`` error is raised. ``http_client_factory``
        is for tests — production code lets the client own the
        ``httpx.Client``.
        """
        if not isinstance(request, GeminiTextTranslateRequest):
            raise TypeError("request must be a GeminiTextTranslateRequest")
        if cancel_check is not None and not callable(cancel_check):
            raise TypeError("cancel_check must be callable when set")

        if not request.segments:
            return GeminiTextTranslateResult(translated={})

        if cancel_check is not None and cancel_check():
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.CANCELLED,
                "translation cancelled before request",
            )

        body = self._build_body(request)
        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            client_cm = (
                http_client_factory(self._timeout)
                if http_client_factory is not None
                else httpx.Client(timeout=self._timeout)
            )
            with client_cm as client:
                response = client.post(url, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.TIMEOUT,
                "translate request timed out",
            ) from exc
        except httpx.HTTPError as exc:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.UPSTREAM,
                f"translate transport error: {type(exc).__name__}",
            ) from exc

        self._raise_for_status(response)

        try:
            payload = response.json()
        except ValueError as exc:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.PROTOCOL,
                "translate response was not valid JSON",
                upstream_snippet=_snippet(response.text),
            ) from exc

        raw_text = self._extract_content_text(payload)
        if not raw_text.strip():
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.PROTOCOL,
                "translate response had empty content",
            )

        translated, repair_used = self._parse_items(raw_text)
        missing = tuple(
            s.index for s in request.segments if s.index not in translated
        )
        return GeminiTextTranslateResult(
            translated=translated,
            missing_indexes=missing,
            json_repair_used=repair_used,
        )

    def _build_body(
        self, request: GeminiTextTranslateRequest
    ) -> dict[str, Any]:
        payload = [
            {"index": int(s.index), "text": str(s.text)}
            for s in request.segments
        ]
        prompt = (
            _PROMPT_HEADER
            + f"target_lang={request.target_lang}\n"
            + f"Input segments: {json.dumps(payload, ensure_ascii=False)}"
        )
        return {
            "model": self._config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a translation engine. Output strict JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

    def _raise_for_status(self, response: httpx.Response) -> None:
        status = response.status_code
        if status < 400:
            return
        snippet = _snippet(response.text)
        if status in (401, 403):
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.AUTH,
                f"translate auth failure (HTTP {status})",
                status=status,
                upstream_snippet=snippet,
            )
        if status == 408:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.TIMEOUT,
                "translate request timed out (HTTP 408)",
                status=status,
                upstream_snippet=snippet,
            )
        if status == 429:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.RATE_LIMITED,
                "translate rate limited (HTTP 429)",
                status=status,
                upstream_snippet=snippet,
            )
        if 400 <= status < 500:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.INVALID_REQUEST,
                f"translate request rejected (HTTP {status})",
                status=status,
                upstream_snippet=snippet,
            )
        raise GeminiTextTranslateError(
            GeminiTextTranslateErrorKind.UPSTREAM,
            f"translate upstream failure (HTTP {status})",
            status=status,
            upstream_snippet=snippet,
        )

    @staticmethod
    def _extract_content_text(payload: Mapping[str, Any]) -> str:
        choices = payload.get("choices") if isinstance(payload, Mapping) else None
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
        candidates = (
            payload.get("candidates") if isinstance(payload, Mapping) else None
        )
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, Mapping):
                content = first.get("content")
                if isinstance(content, Mapping):
                    parts = content.get("parts")
                    if isinstance(parts, list):
                        text = "".join(
                            str(p.get("text") or "")
                            for p in parts
                            if isinstance(p, Mapping)
                        )
                        if text.strip():
                            return text
        return ""

    @staticmethod
    def _parse_items(raw_text: str) -> tuple[dict[int, str], bool]:
        text = (raw_text or "").strip()
        if not text:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.PROTOCOL,
                "translate response had empty content",
            )
        repair_used = False
        fenced = re.search(
            r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE
        )
        if fenced:
            text = fenced.group(1).strip()
            repair_used = True
        match = re.search(r"\{[\s\S]*\}", text)
        if match and match.group(0) != text:
            text = match.group(0).strip()
            repair_used = True
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.PROTOCOL,
                "translate response JSON could not be parsed",
                upstream_snippet=_snippet(raw_text),
            ) from exc
        items = None
        if isinstance(data, Mapping):
            items = data.get("segments")
            if not isinstance(items, list):
                items = data.get("items")
        if not isinstance(items, list):
            raise GeminiTextTranslateError(
                GeminiTextTranslateErrorKind.PROTOCOL,
                "translate response missing 'segments' / 'items' list",
                upstream_snippet=_snippet(raw_text),
            )
        out: dict[int, str] = {}
        for item in items:
            if not isinstance(item, Mapping):
                continue
            try:
                idx = int(item.get("index"))
            except (TypeError, ValueError):
                continue
            translated = str(
                item.get("text") or item.get("translated") or ""
            ).strip()
            if translated:
                out[idx] = translated
        return out, repair_used


def _snippet(text: Optional[str], limit: int = 240) -> Optional[str]:
    if text is None:
        return None
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + "..."

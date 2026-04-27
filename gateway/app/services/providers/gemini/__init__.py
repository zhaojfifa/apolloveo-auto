"""Gemini provider client subpackage (W2.1 first provider absorption).

Donor source: ``backend/app/utils/translate_gemini.py`` (donor pin recorded
in ``docs/donor/swiftcraft_capability_mapping_v1.md`` row A-03 / W2.1 wave
pin row).

Side-effect-free at import: only the provider client class is exposed.
Network, env reads, and credential resolution are invocation-time only and
live behind the worker-side ``UnderstandingAdapter`` binding under
``gateway/app/services/workers/adapters/gemini/``.
"""
from .translate import (
    GeminiTextTranslateClient,
    GeminiTextTranslateConfig,
    GeminiTextTranslateError,
    GeminiTextTranslateErrorKind,
    GeminiTextTranslateRequest,
    GeminiTextTranslateResult,
    GeminiTextTranslateSegment,
)

__all__ = [
    "GeminiTextTranslateClient",
    "GeminiTextTranslateConfig",
    "GeminiTextTranslateError",
    "GeminiTextTranslateErrorKind",
    "GeminiTextTranslateRequest",
    "GeminiTextTranslateResult",
    "GeminiTextTranslateSegment",
]

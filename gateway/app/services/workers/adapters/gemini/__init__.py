"""Gemini worker-side adapter bindings (W2.1 first provider absorption).

Binds the ``gateway/app/services/providers/gemini/`` provider clients into
capability adapter base interfaces under
``gateway/app/services/capability/adapters/``.

W2.1 scope: only ``UnderstandingAdapter`` ← Gemini text translation. No
other capability binding (subtitles / dub / avatar / video_gen / etc.) is
introduced in this wave (W2.1 directive §4.2).
"""
from .understanding import (
    GeminiUnderstandingAdapter,
    GEMINI_API_KEY_REF,
    GEMINI_BASE_URL_REF,
    GEMINI_MODEL_REF,
    GEMINI_LOGICAL_TO_ENV,
)

__all__ = [
    "GeminiUnderstandingAdapter",
    "GEMINI_API_KEY_REF",
    "GEMINI_BASE_URL_REF",
    "GEMINI_MODEL_REF",
    "GEMINI_LOGICAL_TO_ENV",
]

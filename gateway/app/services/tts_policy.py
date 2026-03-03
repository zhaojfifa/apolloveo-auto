from __future__ import annotations

from typing import Any


def normalize_target_lang(value: str | None, default: str = "my") -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    if raw == "mm":
        return "my"
    return raw


def public_target_lang(value: str | None, default: str = "mm") -> str:
    internal = normalize_target_lang(value, default="my")
    if internal == "my":
        return "mm"
    return internal or default


def normalize_provider(provider: str | None, default: str = "edge-tts") -> str:
    raw = str(provider or "").strip().lower().replace("_", "-")
    if raw in {"", "none"}:
        return default
    if raw == "edge":
        return "edge-tts"
    if raw in {"azure", "azure-tts", "azure-speech"}:
        return "azure-speech"
    if raw in {"edge-tts", "lovo"}:
        return raw
    return raw


def _default_voice_for_lang(settings: Any, provider: str, target_lang: str) -> str | None:
    lang = normalize_target_lang(target_lang)
    if lang == "my":
        if provider == "azure-speech":
            return (
                settings.azure_tts_voice_map.get("mm_female_1")
                or settings.edge_tts_voice_map.get("mm_female_1")
                or "my-MM-NilarNeural"
            )
        if provider == "edge-tts":
            return settings.edge_tts_voice_map.get("mm_female_1") or "my-MM-NilarNeural"
        if provider == "lovo":
            return getattr(settings, "lovo_voice_id_mm", None) or "mm_female_1"
    if lang == "zh":
        return "zh-CN-XiaoxiaoNeural"
    if lang == "en":
        return "en-US-ChristopherNeural"
    return None


def is_voice_compatible(target_lang: str | None, voice: str | None) -> bool:
    normalized_lang = normalize_target_lang(target_lang)
    voice_value = str(voice or "").strip()
    if not voice_value:
        return False
    lower_voice = voice_value.lower()
    if normalized_lang == "my":
        return (
            lower_voice.startswith("my-mm-")
            or lower_voice.startswith("mm_")
            or "burmese" in lower_voice
        )
    return True


def resolve_tts_voice(
    *,
    settings: Any,
    provider: str | None,
    target_lang: str | None,
    requested_voice: str | None,
) -> tuple[str | None, bool]:
    provider_name = normalize_provider(provider)
    requested = str(requested_voice or "").strip() or None
    if requested and is_voice_compatible(target_lang, requested):
        return requested, False
    fallback = _default_voice_for_lang(settings, provider_name, normalize_target_lang(target_lang))
    return fallback, bool(requested and fallback and fallback != requested)

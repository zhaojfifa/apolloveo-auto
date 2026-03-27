from __future__ import annotations

from typing import Any

from gateway.app.services.hot_follow_language_profiles import get_hot_follow_language_profile


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
    if lang in {"my", "vi"}:
        profile = get_hot_follow_language_profile(lang)
        default_voice_id = profile.default_voice_id(provider)
        if provider == "azure-speech":
            return (
                settings.azure_tts_voice_map.get(default_voice_id)
                or settings.edge_tts_voice_map.get(default_voice_id)
            )
        if provider == "edge-tts":
            return settings.edge_tts_voice_map.get(default_voice_id)
        if provider == "lovo" and lang == "my":
            if default_voice_id == "mm_female_1":
                return getattr(settings, "lovo_speaker_mm_female_1", None) or getattr(settings, "lovo_voice_id_mm", None) or default_voice_id
            if default_voice_id == "mm_male_1":
                return getattr(settings, "lovo_speaker_mm_male_1", None) or default_voice_id
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
    if normalized_lang == "vi":
        return lower_voice.startswith("vi-vn-") or lower_voice.startswith("vi_") or "vietnamese" in lower_voice
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
    provider_map: dict[str, str] = {}
    if provider_name == "edge-tts":
        provider_map = dict(getattr(settings, "edge_tts_voice_map", {}) or {})
    elif provider_name == "azure-speech":
        provider_map = dict(getattr(settings, "azure_tts_voice_map", {}) or {})
    elif provider_name == "lovo":
        if getattr(settings, "lovo_speaker_mm_female_1", None):
            provider_map["mm_female_1"] = str(getattr(settings, "lovo_speaker_mm_female_1"))
        if getattr(settings, "lovo_speaker_mm_male_1", None):
            provider_map["mm_male_1"] = str(getattr(settings, "lovo_speaker_mm_male_1"))

    if requested and is_voice_compatible(target_lang, requested):
        mapped = provider_map.get(requested)
        if mapped:
            return mapped, mapped != requested
        if requested in provider_map.values():
            return requested, False
        if requested.lower().startswith(("mm_", "vi_")):
            return None, True
        return requested, False
    fallback = _default_voice_for_lang(settings, provider_name, normalize_target_lang(target_lang))
    return fallback, bool(requested and fallback and fallback != requested)

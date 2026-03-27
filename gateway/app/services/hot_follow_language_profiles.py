from __future__ import annotations

from dataclasses import dataclass

def _normalize_provider(provider: str | None, default: str = "edge-tts") -> str:
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


def _normalize_target_lang(value: str | None, default: str = "my") -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    if raw == "mm":
        return "my"
    return raw


@dataclass(frozen=True)
class HotFollowLanguageProfile:
    internal_lang: str
    public_lang: str
    display_name: str
    subtitle_filename: str
    dub_filename: str
    allowed_voice_options: tuple[str, ...]
    default_voice_by_provider: dict[str, str]

    @property
    def subtitle_txt_filename(self) -> str:
        return self.subtitle_filename.rsplit(".", 1)[0] + ".txt"

    def default_voice_id(self, provider: str | None = None) -> str:
        provider_name = _normalize_provider(provider, default="azure-speech")
        return (
            self.default_voice_by_provider.get(provider_name)
            or self.default_voice_by_provider.get("azure-speech")
            or self.allowed_voice_options[0]
        )

    def supported_providers(self) -> tuple[str, ...]:
        ordered = []
        for name in ("azure-speech", "edge-tts", "lovo"):
            if name in self.default_voice_by_provider and name not in ordered:
                ordered.append(name)
        return tuple(ordered)


_MYANMAR = HotFollowLanguageProfile(
    internal_lang="my",
    public_lang="mm",
    display_name="Myanmar",
    subtitle_filename="mm.srt",
    dub_filename="audio_mm.mp3",
    allowed_voice_options=("mm_female_1", "mm_male_1"),
    default_voice_by_provider={
        "azure-speech": "mm_female_1",
        "edge-tts": "mm_female_1",
        "lovo": "mm_female_1",
    },
)

_VIETNAMESE = HotFollowLanguageProfile(
    internal_lang="vi",
    public_lang="vi",
    display_name="Tiếng Việt",
    subtitle_filename="vi.srt",
    dub_filename="audio_vi.mp3",
    allowed_voice_options=("vi_female_1", "vi_male_1"),
    default_voice_by_provider={
        "azure-speech": "vi_female_1",
        "edge-tts": "vi_female_1",
    },
)

_PROFILES = {
    "my": _MYANMAR,
    "mm": _MYANMAR,
    "vi": _VIETNAMESE,
}


def get_hot_follow_language_profile(target_lang: str | None) -> HotFollowLanguageProfile:
    normalized = _normalize_target_lang(target_lang, default="my")
    return _PROFILES.get(normalized, _MYANMAR)


def list_hot_follow_language_profiles() -> list[dict[str, object]]:
    profiles = [_MYANMAR, _VIETNAMESE]
    return [
        {
            "target_lang": profile.public_lang,
            "internal_lang": profile.internal_lang,
            "display_name": profile.display_name,
            "subtitle_filename": profile.subtitle_filename,
            "subtitle_txt_filename": profile.subtitle_txt_filename,
            "dub_filename": profile.dub_filename,
            "allowed_voice_options": list(profile.allowed_voice_options),
            "supported_providers": list(profile.supported_providers()),
            "default_voice_by_provider": dict(profile.default_voice_by_provider),
        }
        for profile in profiles
    ]


def hot_follow_subtitle_filename(target_lang: str | None) -> str:
    return get_hot_follow_language_profile(target_lang).subtitle_filename


def hot_follow_subtitle_txt_filename(target_lang: str | None) -> str:
    return get_hot_follow_language_profile(target_lang).subtitle_txt_filename


def hot_follow_audio_filename(target_lang: str | None) -> str:
    return get_hot_follow_language_profile(target_lang).dub_filename


def hot_follow_public_lang(target_lang: str | None) -> str:
    profile = get_hot_follow_language_profile(target_lang)
    return profile.public_lang


def hot_follow_internal_lang(target_lang: str | None) -> str:
    return get_hot_follow_language_profile(target_lang).internal_lang


def resolve_hot_follow_voice_id(target_lang: str | None, requested_voice: str | None, provider: str | None = None) -> str:
    profile = get_hot_follow_language_profile(target_lang)
    requested = str(requested_voice or "").strip()
    if requested in profile.allowed_voice_options:
        return requested
    return profile.default_voice_id(provider)

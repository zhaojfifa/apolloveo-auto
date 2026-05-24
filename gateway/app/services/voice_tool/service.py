from __future__ import annotations

import asyncio
import re
from pathlib import Path
from uuid import uuid4

from gateway.app.providers.azure_speech import AzureSpeechError, generate_audio_azure_speech
from gateway.app.services.providers.gemini import (
    GeminiTextTranslateClient,
    GeminiTextTranslateConfig,
    GeminiTextTranslateError,
    GeminiTextTranslateRequest,
    GeminiTextTranslateSegment,
)

from .models import (
    FAILURE_REASONS,
    LANGUAGE_NAMES,
    SOURCE_LANGUAGES,
    SPEED_PRESETS,
    STYLE_PRESETS,
    TARGET_LANGUAGES,
    USABLE_FOR_PUBLISH_VALUES,
    VOICE_MODES,
    VOICE_PRESETS,
    VoiceToolFeedback,
    VoiceToolJob,
)
from .storage import VoiceToolStorage


class VoiceToolError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class VoiceToolService:
    def __init__(
        self,
        *,
        storage: VoiceToolStorage,
        translate_client: GeminiTextTranslateClient | None = None,
        settings_obj=None,
        tts_func=generate_audio_azure_speech,
    ) -> None:
        self.storage = storage
        self._translate_client = translate_client
        self._settings = settings_obj or _get_settings()
        self._tts_func = tts_func

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        style_preset: str,
    ) -> VoiceToolJob:
        self._validate_text(source_text)
        self._validate_language(source_language, SOURCE_LANGUAGES, "source_language")
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        self._validate_choice(style_preset, STYLE_PRESETS, "style_preset")

        job = VoiceToolJob(
            job_id=_new_job_id(),
            source_text=source_text.strip(),
            source_language=source_language,
            target_language=target_language,
            style_preset=style_preset,
        )
        translated = self._translate_text(
            source_text=job.source_text,
            source_language=source_language,
            target_language=target_language,
        )
        job.translated_text = translated
        job.speech_text = self.rewrite_speech_text(
            translated_text=translated,
            target_language=target_language,
            style_preset=style_preset,
            voice_mode="humanized",
        )
        job.provider_used_backend_only["translation"] = "gemini"
        job.provider_used_backend_only["speech_rewrite"] = "gemini"
        return self.storage.write_job(job)

    def rewrite_speech_text(
        self,
        *,
        translated_text: str,
        target_language: str,
        style_preset: str,
        voice_mode: str = "humanized",
    ) -> str:
        self._validate_text(translated_text)
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        self._validate_choice(style_preset, STYLE_PRESETS, "style_preset")
        self._validate_choice(voice_mode, VOICE_MODES, "voice_mode")
        rewritten = self._rewrite_text(
            translated_text=translated_text.strip(),
            target_language=target_language,
            style_preset=style_preset,
            voice_mode=voice_mode,
        )
        return rewritten

    def generate_style_variants(
        self,
        *,
        translated_text: str | None = None,
        target_language: str,
        voice_mode: str = "humanized",
        job_id: str | None = None,
    ) -> dict[str, str]:
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        self._validate_choice(voice_mode, VOICE_MODES, "voice_mode")
        job = self.storage.read_job(job_id) if job_id else None
        base_text = translated_text if translated_text is not None else (job.translated_text if job else "")
        self._validate_text(base_text)
        variants = {
            style: self.rewrite_speech_text(
                translated_text=base_text,
                target_language=target_language,
                style_preset=style,
                voice_mode=voice_mode,
            )
            for style in ("natural_human", "sales", "explainer", "news", "calm")
        }
        if job is not None:
            job.speech_variants = variants
            self.storage.write_job(job)
        return variants

    async def synthesize(
        self,
        *,
        speech_text: str,
        target_language: str,
        voice_preset: str,
        speed: str,
        voice_mode: str = "stable",
        job_id: str | None = None,
    ) -> VoiceToolJob:
        self._validate_text(speech_text)
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        self._validate_choice(voice_preset, VOICE_PRESETS, "voice_preset")
        self._validate_choice(voice_mode, VOICE_MODES, "voice_mode")
        self._validate_choice(speed, SPEED_PRESETS, "speed")

        if job_id:
            job = self.storage.read_job(job_id)
            job.speech_text = speech_text.strip()
            job.target_language = target_language
        else:
            job = VoiceToolJob(
                job_id=_new_job_id(),
                source_text="",
                source_language="",
                target_language=target_language,
                speech_text=speech_text.strip(),
            )
        job.voice_preset = voice_preset
        job.voice_mode = voice_mode
        job.speed = speed

        paths = self.storage.paths_for(job.job_id)
        paths.root.mkdir(parents=True, exist_ok=True)
        voice = _resolve_voice(self._settings, target_language, voice_preset)
        try:
            await asyncio.wait_for(
                self._tts_func(
                    job.speech_text,
                    voice,
                    str(paths.output_mp3),
                    speech_key=getattr(self._settings, "azure_speech_key", ""),
                    speech_region=getattr(self._settings, "azure_speech_region", ""),
                    output_format=getattr(
                        self._settings,
                        "azure_tts_output_format",
                        "audio-24khz-48kbitrate-mono-mp3",
                    ),
                    rate=_azure_rate(speed),
                ),
                timeout=120,
            )
        except TypeError:
            await self._tts_func(
                job.speech_text,
                voice,
                str(paths.output_mp3),
                speech_key=getattr(self._settings, "azure_speech_key", ""),
                speech_region=getattr(self._settings, "azure_speech_region", ""),
                output_format=getattr(
                    self._settings,
                    "azure_tts_output_format",
                    "audio-24khz-48kbitrate-mono-mp3",
                ),
            )
        except AzureSpeechError as exc:
            raise VoiceToolError("tts_failed", str(exc)) from exc
        except asyncio.TimeoutError as exc:
            raise VoiceToolError("tts_timeout", "Azure speech synthesis timed out") from exc

        if not paths.output_mp3.exists() or paths.output_mp3.stat().st_size <= 0:
            raise VoiceToolError("tts_empty_audio", "Azure speech returned no audio")

        job.audio_path = str(paths.output_mp3)
        job.provider_used_backend_only["tts"] = "azure_speech"
        return self.storage.write_job(job)

    async def generate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        style_preset: str,
        voice_preset: str,
        speed: str,
        voice_mode: str = "stable",
    ) -> VoiceToolJob:
        job = self.translate(
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
            style_preset=style_preset,
        )
        job.speech_text = self.rewrite_speech_text(
            translated_text=job.translated_text,
            target_language=target_language,
            style_preset=style_preset,
            voice_mode=voice_mode,
        )
        job.voice_mode = voice_mode
        self.storage.write_job(job)
        return await self.synthesize(
            job_id=job.job_id,
            speech_text=job.speech_text,
            target_language=target_language,
            voice_preset=voice_preset,
            voice_mode=voice_mode,
            speed=speed,
        )

    def get_job(self, job_id: str) -> VoiceToolJob:
        return self.storage.read_job(job_id)

    def public_options(self, target_language: str) -> dict[str, object]:
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        return {
            "target_language": target_language,
            "voice_options": _public_voice_options(self._settings, target_language),
            "voice_modes": [
                {"value": "stable", "label": "标准稳定"},
                {"value": "humanized", "label": "拟人增强（口播文本优化）"},
            ],
        }

    def submit_feedback(
        self,
        *,
        job_id: str,
        naturalness_score: int,
        translation_score: int,
        speed_score: int,
        voice_fit_score: int,
        usable_for_publish: str,
        failure_reason: str | None = None,
        comment: str = "",
    ) -> VoiceToolJob:
        for name, value in {
            "naturalness_score": naturalness_score,
            "translation_score": translation_score,
            "speed_score": speed_score,
            "voice_fit_score": voice_fit_score,
        }.items():
            if not isinstance(value, int) or value < 1 or value > 5:
                raise VoiceToolError("invalid_feedback", f"{name} must be 1-5")
        self._validate_choice(
            usable_for_publish, USABLE_FOR_PUBLISH_VALUES, "usable_for_publish"
        )
        if failure_reason:
            self._validate_choice(failure_reason, FAILURE_REASONS, "failure_reason")
        job = self.storage.read_job(job_id)
        feedback = VoiceToolFeedback(
            naturalness_score=naturalness_score,
            translation_score=translation_score,
            speed_score=speed_score,
            voice_fit_score=voice_fit_score,
            usable_for_publish=usable_for_publish,
            failure_reason=failure_reason or None,
            comment=comment.strip(),
        )
        return self.storage.write_feedback(job, feedback)

    def _translate_text(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        client = self._translate_client or self._build_gemini_client()
        target_name = LANGUAGE_NAMES[target_language]
        source_name = LANGUAGE_NAMES.get(source_language, source_language)
        target_hint = (
            f"{target_name}; source language is {source_name}; "
            "faithful semantic translation only; preserve facts; "
            "do not apply marketing, news, calm, or conversational style"
        )
        try:
            result = client.translate_segments(
                GeminiTextTranslateRequest(
                    segments=(GeminiTextTranslateSegment(index=1, text=source_text),),
                    target_lang=target_hint,
                )
            )
        except GeminiTextTranslateError as exc:
            raise VoiceToolError("translation_failed", str(exc)) from exc
        translated = str(result.translated.get(1) or "").strip()
        if not translated:
            raise VoiceToolError("translation_empty", "Gemini returned no translated text")
        return translated

    def _rewrite_text(
        self,
        *,
        translated_text: str,
        target_language: str,
        style_preset: str,
        voice_mode: str,
    ) -> str:
        client = self._translate_client or self._build_gemini_client()
        target_name = LANGUAGE_NAMES[target_language]
        prompt_hint = _speech_rewrite_prompt(
            target_language=target_language,
            target_name=target_name,
            style_preset=style_preset,
            voice_mode=voice_mode,
        )
        try:
            result = client.translate_segments(
                GeminiTextTranslateRequest(
                    segments=(GeminiTextTranslateSegment(index=1, text=translated_text),),
                    target_lang=prompt_hint,
                )
            )
        except GeminiTextTranslateError as exc:
            raise VoiceToolError("speech_rewrite_failed", str(exc)) from exc
        rewritten = str(result.translated.get(1) or "").strip()
        if not rewritten:
            raise VoiceToolError("speech_rewrite_empty", "Gemini returned no speech text")
        return rewritten

    def _build_gemini_client(self) -> GeminiTextTranslateClient:
        api_key = getattr(self._settings, "gemini_api_key", None)
        if not api_key:
            raise VoiceToolError("translation_config_missing", "GEMINI_API_KEY is not configured")
        return GeminiTextTranslateClient(
            GeminiTextTranslateConfig(
                api_key=str(api_key),
                base_url=str(getattr(self._settings, "gemini_base_url", "")),
                model=str(getattr(self._settings, "gemini_model", "gemini-2.0-flash")),
                timeout_seconds=45.0,
            )
        )

    @staticmethod
    def _validate_text(value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise VoiceToolError("invalid_text", "text must be non-empty")
        if len(value.strip()) > 8000:
            raise VoiceToolError("invalid_text", "text is too long")

    @staticmethod
    def _validate_language(value: str, allowed: frozenset[str], field_name: str) -> None:
        if value not in allowed:
            raise VoiceToolError("invalid_language", f"{field_name} is not supported")

    @staticmethod
    def _validate_choice(value: str, allowed: frozenset[str], field_name: str) -> None:
        if value not in allowed:
            raise VoiceToolError("invalid_choice", f"{field_name} is not supported")


def _new_job_id() -> str:
    return f"vt_{uuid4().hex}"


def _shape_speech_text(text: str, style_preset: str) -> str:
    shaped = re.sub(r"\s+", " ", str(text or "")).strip()
    if style_preset == "news":
        return shaped
    if style_preset == "calm":
        return shaped.replace("!", ".")
    return shaped


STYLE_REWRITE_RULES = {
    "natural_human": (
        "Natural local human speech: conversational, less written, smooth for a "
        "real presenter, with small spoken transitions when helpful."
    ),
    "sales": (
        "Persuasive product or marketing expression: stronger conversion tone, "
        "clear benefit framing, but do not invent product facts."
    ),
    "explainer": (
        "Clear structured explanation: easy to understand, orderly, suitable "
        "for instructional voiceover."
    ),
    "news": (
        "Formal objective broadcast style: concise, neutral, no hype, suitable "
        "for news reading."
    ),
    "calm": (
        "Gentle, clear, slower and steady expression: warm but not exaggerated."
    ),
}


LANGUAGE_REWRITE_RULES = {
    "my": (
        "Use natural Burmese phrasing for spoken delivery. Avoid over-literal "
        "translation from Chinese or English. Keep local speech rhythm."
    ),
    "vi": (
        "Use natural Vietnamese phrasing for spoken delivery. Avoid word-for-word "
        "translation. Keep the sentence flow local and easy to read aloud."
    ),
}


def _speech_rewrite_prompt(
    *,
    target_language: str,
    target_name: str,
    style_preset: str,
    voice_mode: str,
) -> str:
    humanized_rule = (
        "Use a more human, oral wording pass."
        if voice_mode == "humanized"
        else "Keep wording stable and conservative while still suitable for speech."
    )
    return (
        f"{target_name} speech rewrite; style={style_preset}. "
        f"{STYLE_REWRITE_RULES[style_preset]} "
        f"{LANGUAGE_REWRITE_RULES[target_language]} "
        "Preserve original meaning. Do not add unsupported factual claims. "
        "Keep length close to the translated text unless the selected style "
        "requires mild expansion. For sales style, allow moderate persuasive "
        "phrasing without changing product facts. "
        f"{humanized_rule} Return only the rewritten speech text."
    )


def _resolve_voice(settings_obj, target_language: str, voice_preset: str) -> str:
    gender = "female" if voice_preset == "natural" else voice_preset
    prefix = "mm" if target_language == "my" else "vi"
    voice_key = f"{prefix}_{gender}_1"
    voice_map = getattr(settings_obj, "azure_tts_voice_map", {}) or {}
    voice = voice_map.get(voice_key)
    if not voice:
        fallback_key = f"{prefix}_female_1"
        voice = voice_map.get(fallback_key)
    if not voice:
        defaults = {
            "my": "my-MM-NilarNeural",
            "vi": "vi-VN-HoaiMyNeural",
        }
        voice = defaults[target_language]
    return str(voice)


def _public_voice_options(settings_obj, target_language: str) -> list[dict[str, str]]:
    labels = {
        "natural": "自然音色",
        "female": "女声",
        "male": "男声",
    }
    options: list[dict[str, str]] = []
    seen_voices: set[str] = set()
    for preset in ("natural", "female", "male"):
        voice = _resolve_voice(settings_obj, target_language, preset)
        if voice in seen_voices:
            continue
        seen_voices.add(voice)
        options.append({"value": preset, "label": labels[preset]})
    return options


def _azure_rate(speed: str) -> str:
    return {
        "slow": "-12%",
        "normal": "+0%",
        "fast": "+12%",
    }[speed]


def get_voice_tool_service() -> VoiceToolService:
    settings_obj = _get_settings()
    root = (
        Path(getattr(settings_obj, "workspace_root", "./data_debug"))
        / "artifacts"
        / "voice_tool"
    )
    return VoiceToolService(storage=VoiceToolStorage(root), settings_obj=settings_obj)


def _get_settings():
    from gateway.app.config import get_settings

    return get_settings()

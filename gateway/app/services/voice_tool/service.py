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
    EXPRESSION_STYLES,
    FAILURE_REASONS,
    LANGUAGE_NAMES,
    SPEAKER_GENDERS,
    SOURCE_LANGUAGES,
    SPEED_PRESETS,
    STYLE_PRESETS,
    TARGET_LANGUAGES,
    USABLE_FOR_PUBLISH_VALUES,
    USAGE_SCENES,
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
        style_preset: str | None = None,
        speaker_gender: str = "female",
        expression_style: str | None = None,
        usage_scene: str = "short_video_voiceover",
        custom_humanize_prompt: str = "",
    ) -> VoiceToolJob:
        self._validate_text(source_text)
        self._validate_language(source_language, SOURCE_LANGUAGES, "source_language")
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        expression_style = _normalize_expression_style(expression_style, style_preset)
        style_preset = _style_preset_from_expression(expression_style)
        self._validate_choice(speaker_gender, SPEAKER_GENDERS, "speaker_gender")
        self._validate_choice(expression_style, EXPRESSION_STYLES, "expression_style")
        self._validate_choice(usage_scene, USAGE_SCENES, "usage_scene")

        job = VoiceToolJob(
            job_id=_new_job_id(),
            source_text=source_text.strip(),
            source_language=source_language,
            target_language=target_language,
            style_preset=style_preset,
            voice_preset=speaker_gender,
            speaker_gender=speaker_gender,
            expression_style=expression_style,
            usage_scene=usage_scene,
            custom_humanize_prompt=custom_humanize_prompt.strip(),
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
            expression_style=expression_style,
            usage_scene=usage_scene,
            speaker_gender=speaker_gender,
            custom_humanize_prompt=custom_humanize_prompt,
            voice_mode="humanized",
        )
        job.provider_used_backend_only["translation"] = "gemini"
        job.provider_used_backend_only["speech_rewrite"] = "gemini"
        _record_stage_provider(job, "semantic_translation", "gemini")
        _record_stage_provider(job, "speech_rewrite", "gemini")
        return self.storage.write_job(job)

    def rewrite_speech_text(
        self,
        *,
        translated_text: str,
        target_language: str,
        style_preset: str | None = None,
        speaker_gender: str = "female",
        expression_style: str | None = None,
        usage_scene: str = "short_video_voiceover",
        custom_humanize_prompt: str = "",
        voice_mode: str = "humanized",
    ) -> str:
        self._validate_text(translated_text)
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        expression_style = _normalize_expression_style(expression_style, style_preset)
        self._validate_choice(speaker_gender, SPEAKER_GENDERS, "speaker_gender")
        self._validate_choice(expression_style, EXPRESSION_STYLES, "expression_style")
        self._validate_choice(usage_scene, USAGE_SCENES, "usage_scene")
        self._validate_choice(voice_mode, VOICE_MODES, "voice_mode")
        rewritten = self._rewrite_text(
            translated_text=translated_text.strip(),
            target_language=target_language,
            speaker_gender=speaker_gender,
            expression_style=expression_style,
            usage_scene=usage_scene,
            custom_humanize_prompt=custom_humanize_prompt.strip(),
            voice_mode=voice_mode,
        )
        return rewritten

    def generate_style_variants(
        self,
        *,
        translated_text: str | None = None,
        target_language: str,
        speaker_gender: str = "female",
        usage_scene: str = "short_video_voiceover",
        custom_humanize_prompt: str = "",
        voice_mode: str = "humanized",
        job_id: str | None = None,
    ) -> dict[str, str]:
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        self._validate_choice(speaker_gender, SPEAKER_GENDERS, "speaker_gender")
        self._validate_choice(usage_scene, USAGE_SCENES, "usage_scene")
        self._validate_choice(voice_mode, VOICE_MODES, "voice_mode")
        job = self.storage.read_job(job_id) if job_id else None
        base_text = translated_text if translated_text is not None else (job.translated_text if job else "")
        self._validate_text(base_text)
        variants = {
            style: self.rewrite_speech_text(
                translated_text=base_text,
                target_language=target_language,
                speaker_gender=speaker_gender,
                expression_style=style,
                usage_scene=usage_scene,
                custom_humanize_prompt=custom_humanize_prompt,
                voice_mode=voice_mode,
            )
            for style in ("natural", "professional", "engaging")
        }
        if job is not None:
            _record_stage_provider(job, "speech_rewrite", "gemini")
            job.speech_variants = variants
            job.speaker_gender = speaker_gender
            job.expression_style = job.expression_style or "natural"
            job.usage_scene = usage_scene
            job.custom_humanize_prompt = custom_humanize_prompt.strip()
            self.storage.write_job(job)
        return variants

    async def synthesize(
        self,
        *,
        speech_text: str,
        target_language: str,
        voice_preset: str | None = None,
        speaker_gender: str | None = None,
        speed: str = "normal",
        voice_mode: str = "stable",
        job_id: str | None = None,
    ) -> VoiceToolJob:
        self._validate_text(speech_text)
        self._validate_language(target_language, TARGET_LANGUAGES, "target_language")
        speaker_gender = _normalize_speaker_gender(speaker_gender, voice_preset)
        self._validate_choice(speaker_gender, SPEAKER_GENDERS, "speaker_gender")
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
        job.voice_preset = speaker_gender
        job.speaker_gender = speaker_gender
        job.voice_mode = voice_mode
        job.speed = speed
        _record_stage_provider(job, "speech_synthesis", "azure_speech")

        paths = self.storage.paths_for(job.job_id)
        paths.root.mkdir(parents=True, exist_ok=True)
        voice = _resolve_voice(self._settings, target_language, speaker_gender)
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
        except TypeError as exc:
            try:
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
            except Exception as fallback_exc:
                _record_stage_error(job, "speech_synthesis", str(fallback_exc))
                self.storage.write_job(job)
                raise VoiceToolError("tts_failed", str(fallback_exc)) from fallback_exc
        except AzureSpeechError as exc:
            _record_stage_error(job, "speech_synthesis", str(exc))
            self.storage.write_job(job)
            raise VoiceToolError("tts_failed", str(exc)) from exc
        except asyncio.TimeoutError as exc:
            _record_stage_error(job, "speech_synthesis", "Azure speech synthesis timed out")
            self.storage.write_job(job)
            raise VoiceToolError("tts_timeout", "Azure speech synthesis timed out") from exc

        if not paths.output_mp3.exists() or paths.output_mp3.stat().st_size <= 0:
            _record_stage_error(job, "speech_synthesis", "Azure speech returned no audio")
            self.storage.write_job(job)
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
        style_preset: str | None = None,
        voice_preset: str | None = None,
        speaker_gender: str | None = None,
        expression_style: str | None = None,
        usage_scene: str = "short_video_voiceover",
        custom_humanize_prompt: str = "",
        speed: str = "normal",
        voice_mode: str = "stable",
    ) -> VoiceToolJob:
        speaker_gender = _normalize_speaker_gender(speaker_gender, voice_preset)
        expression_style = _normalize_expression_style(expression_style, style_preset)
        job = self.translate(
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
            speaker_gender=speaker_gender,
            expression_style=expression_style,
            usage_scene=usage_scene,
            custom_humanize_prompt=custom_humanize_prompt,
        )
        job.speech_text = self.rewrite_speech_text(
            translated_text=job.translated_text,
            target_language=target_language,
            speaker_gender=speaker_gender,
            expression_style=expression_style,
            usage_scene=usage_scene,
            custom_humanize_prompt=custom_humanize_prompt,
            voice_mode=voice_mode,
        )
        _record_stage_provider(job, "speech_rewrite", "gemini")
        job.voice_mode = voice_mode
        self.storage.write_job(job)
        return await self.synthesize(
            job_id=job.job_id,
            speech_text=job.speech_text,
            target_language=target_language,
            speaker_gender=speaker_gender,
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
            "expression_styles": [
                {"value": "natural", "label": "自然"},
                {"value": "professional", "label": "专业"},
                {"value": "engaging", "label": "有感染力"},
            ],
            "usage_scenes": [
                {"value": "short_video_voiceover", "label": "短视频口播"},
                {"value": "product_intro", "label": "商品介绍"},
            ],
            "voice_modes": [
                {"value": "stable", "label": "标准稳定"},
                {"value": "humanized", "label": "拟人增强（口播文本优化）"},
            ],
        }

    @staticmethod
    def legacy_style_for_expression(expression_style: str) -> str:
        VoiceToolService._validate_choice(
            expression_style, EXPRESSION_STYLES, "expression_style"
        )
        return _style_preset_from_expression(expression_style)

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
        speaker_gender: str,
        expression_style: str,
        usage_scene: str,
        custom_humanize_prompt: str,
        voice_mode: str,
    ) -> str:
        client = self._translate_client or self._build_gemini_client()
        target_name = LANGUAGE_NAMES[target_language]
        prompt_hint = _speech_rewrite_prompt(
            target_language=target_language,
            target_name=target_name,
            speaker_gender=speaker_gender,
            expression_style=expression_style,
            usage_scene=usage_scene,
            custom_humanize_prompt=custom_humanize_prompt,
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


def _record_stage_provider(job: VoiceToolJob, stage: str, provider: str) -> None:
    job.stage_providers_backend_only[stage] = provider


def _record_stage_error(job: VoiceToolJob, stage: str, error: str) -> None:
    job.stage_errors_backend_only[stage] = str(error or "").strip() or "unknown_error"


def _normalize_speaker_gender(
    speaker_gender: str | None, voice_preset: str | None = None
) -> str:
    value = speaker_gender or voice_preset or "female"
    if value == "natural":
        return "female"
    return value


def _normalize_expression_style(
    expression_style: str | None, style_preset: str | None = None
) -> str:
    if expression_style:
        return expression_style
    if style_preset and style_preset not in STYLE_PRESETS:
        raise VoiceToolError("invalid_choice", "style_preset is not supported")
    return {
        "natural_human": "natural",
        "calm": "natural",
        "explainer": "professional",
        "news": "professional",
        "sales": "engaging",
    }.get(style_preset or "", "natural")


def _style_preset_from_expression(expression_style: str) -> str:
    return {
        "natural": "natural_human",
        "professional": "explainer",
        "engaging": "sales",
    }[expression_style]


def _shape_speech_text(text: str, style_preset: str) -> str:
    shaped = re.sub(r"\s+", " ", str(text or "")).strip()
    if style_preset == "news":
        return shaped
    if style_preset == "calm":
        return shaped.replace("!", ".")
    return shaped


STYLE_REWRITE_RULES = {
    "natural": (
        "Natural local human host delivery: conversational, warm, relaxed, "
        "not mechanical, with wording a local presenter would comfortably say."
    ),
    "professional": (
        "Professional host delivery: clear, credible, structured, suitable for "
        "product explanation without sounding stiff or overly written."
    ),
    "engaging": (
        "Engaging local host delivery: energetic and persuasive for short video "
        "or product intro, but do not invent claims or change product facts."
    ),
}


USAGE_SCENE_RULES = {
    "short_video_voiceover": (
        "Scene: short video voiceover. Keep sentences easy to speak, rhythmic, "
        "and suitable for a concise host read."
    ),
    "product_intro": (
        "Scene: product intro. Make benefits clear and easy to understand. "
        "For engaging style, moderate persuasive wording is allowed without "
        "changing facts."
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
    speaker_gender: str,
    expression_style: str,
    usage_scene: str,
    custom_humanize_prompt: str,
    voice_mode: str,
) -> str:
    humanized_rule = (
        "Use a more human, oral wording pass."
        if voice_mode == "humanized"
        else "Keep wording stable and conservative while still suitable for speech."
    )
    return (
        f"{target_name} humanized speech rewrite; expression_style={expression_style}; "
        f"speaker_gender={speaker_gender}; usage_scene={usage_scene}. "
        f"{STYLE_REWRITE_RULES[expression_style]} "
        f"{USAGE_SCENE_RULES[usage_scene]} "
        f"{LANGUAGE_REWRITE_RULES[target_language]} "
        "Output should sound like a local Burmese or Vietnamese human host. "
        "Avoid machine translation tone. Avoid overly written language. "
        "Keep suitable for short video spoken delivery. Preserve product facts "
        "and core meaning. Do not invent claims. Respect speaker_gender only "
        "as delivery style and voice selection; do not alter factual content. "
        f"{_custom_prompt_rule(custom_humanize_prompt)} "
        f"{humanized_rule} Return only the rewritten speech text."
    )


def _custom_prompt_rule(custom_humanize_prompt: str) -> str:
    prompt = str(custom_humanize_prompt or "").strip()
    if not prompt:
        return ""
    return f"Operator humanization note: {prompt[:600]}"


def _resolve_voice(settings_obj, target_language: str, voice_preset: str) -> str:
    gender = _normalize_speaker_gender(None, voice_preset)
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
        "female": "女主播",
        "male": "男主播",
    }
    options: list[dict[str, str]] = []
    seen_voices: set[str] = set()
    for preset in ("female", "male"):
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

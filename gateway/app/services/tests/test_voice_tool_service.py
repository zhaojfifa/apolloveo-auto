from __future__ import annotations

import json
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from gateway.app.providers.azure_speech import AzureSpeechError
from gateway.app.services.providers.gemini import GeminiTextTranslateResult
from gateway.app.services.voice_tool import VoiceToolError, VoiceToolService
from gateway.app.services.voice_tool.service import STYLE_REWRITE_RULES
from gateway.app.services.voice_tool.storage import VoiceToolStorage


class FakeTranslateClient:
    def __init__(self) -> None:
        self.requests = []

    def translate_segments(self, request):
        self.requests.append(request)
        hint = request.target_lang
        if "faithful semantic translation only" in hint:
            return GeminiTextTranslateResult(translated={1: "တည်ငြိမ်သော ဘာသာပြန်စာသား။"})
        for style in STYLE_REWRITE_RULES:
            if f"expression_style={style}" in hint:
                return GeminiTextTranslateResult(translated={1: f"{style} speech text"})
        return GeminiTextTranslateResult(translated={1: "fallback speech text"})


async def fake_tts(text, voice, output_path, **kwargs):
    Path(output_path).write_bytes(b"fake-mp3-audio")


async def fake_tts_failure(text, voice, output_path, **kwargs):
    raise AzureSpeechError("synthetic synthesis failure")


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        azure_speech_key="test-key",
        azure_speech_region="eastasia",
        azure_tts_output_format="audio-24khz-48kbitrate-mono-mp3",
        azure_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
            "vi_female_1": "vi-VN-HoaiMyNeural",
            "vi_male_1": "vi-VN-NamMinhNeural",
        },
        gemini_api_key="test-gemini",
        gemini_base_url="https://example.invalid/v1beta",
        gemini_model="gemini-test",
        workspace_root="/tmp/unused",
    )


def _service(tmp_path: Path, client: FakeTranslateClient | None = None) -> VoiceToolService:
    return VoiceToolService(
        storage=VoiceToolStorage(tmp_path / "artifacts" / "voice_tool"),
        translate_client=client or FakeTranslateClient(),
        settings_obj=_settings(),
        tts_func=fake_tts,
    )


def test_translate_validates_request_and_writes_manifest(tmp_path: Path) -> None:
    client = FakeTranslateClient()
    service = _service(tmp_path, client)

    job = service.translate(
        source_text="你好，欢迎来到今天的介绍。",
        source_language="zh",
        target_language="my",
        style_preset="natural_human",
    )

    paths = service.storage.paths_for(job.job_id)
    assert paths.source.read_text(encoding="utf-8") == "你好，欢迎来到今天的介绍。"
    assert paths.translated.read_text(encoding="utf-8") == job.translated_text
    assert paths.speech_text.read_text(encoding="utf-8") == job.speech_text
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    assert manifest["target_language"] == "my"
    assert manifest["provider_used_backend_only"] == {
        "translation": "gemini",
        "speech_rewrite": "gemini",
    }
    assert manifest["stage_providers_backend_only"] == {
        "semantic_translation": "gemini",
        "speech_rewrite": "gemini",
    }
    assert "provider_used_backend_only" not in service.storage.public_job_payload(job)
    assert "stage_providers_backend_only" not in service.storage.public_job_payload(job)
    assert "stage_errors_backend_only" not in service.storage.public_job_payload(job)
    assert "Burmese" in client.requests[0].target_lang
    assert "style preset" not in client.requests[0].target_lang
    assert "expression_style=natural" in client.requests[1].target_lang
    assert "speaker_gender=female" in client.requests[1].target_lang
    assert "usage_scene=short_video_voiceover" in client.requests[1].target_lang


def test_translate_rejects_unsupported_target_language(tmp_path: Path) -> None:
    service = _service(tmp_path)

    with pytest.raises(VoiceToolError) as exc:
        service.translate(
            source_text="hello",
            source_language="en",
            target_language="zh",
            style_preset="natural_human",
        )

    assert exc.value.code == "invalid_language"


def test_synthesize_updates_existing_job_and_hides_provider_boundary(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="my",
        style_preset="calm",
    )

    updated = asyncio.run(
        service.synthesize(
            job_id=job.job_id,
            speech_text="မင်္ဂလာပါ။",
            target_language="my",
            voice_preset="female",
            speed="slow",
        )
    )

    paths = service.storage.paths_for(job.job_id)
    assert paths.output_mp3.read_bytes() == b"fake-mp3-audio"
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    assert manifest["provider_used_backend_only"] == {
        "translation": "gemini",
        "speech_rewrite": "gemini",
        "tts": "azure_speech",
    }
    assert manifest["stage_providers_backend_only"] == {
        "semantic_translation": "gemini",
        "speech_rewrite": "gemini",
        "speech_synthesis": "azure_speech",
    }
    public = service.storage.public_job_payload(updated)
    assert public["download_mp3_url"] == f"/api/voice-tool/download/{job.job_id}?format=mp3"
    assert "provider_used_backend_only" not in public
    assert "stage_providers_backend_only" not in public
    assert "stage_errors_backend_only" not in public
    assert public["voice_mode"] == "stable"


def test_synthesize_failure_persists_stage_error_without_audio(tmp_path: Path) -> None:
    service = VoiceToolService(
        storage=VoiceToolStorage(tmp_path / "artifacts" / "voice_tool"),
        translate_client=FakeTranslateClient(),
        settings_obj=_settings(),
        tts_func=fake_tts_failure,
    )
    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="my",
        style_preset="calm",
    )

    with pytest.raises(VoiceToolError) as exc:
        asyncio.run(
            service.synthesize(
                job_id=job.job_id,
                speech_text="မင်္ဂလာပါ။",
                target_language="my",
                voice_preset="female",
                speed="normal",
            )
        )

    assert exc.value.code == "tts_failed"
    paths = service.storage.paths_for(job.job_id)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    assert manifest["stage_providers_backend_only"]["speech_synthesis"] == "azure_speech"
    assert (
        manifest["stage_errors_backend_only"]["speech_synthesis"]
        == "synthetic synthesis failure"
    )
    assert not paths.output_mp3.exists()
    assert service.storage.public_job_payload(service.get_job(job.job_id))["audio_ready"] is False


def test_feedback_persists_json_and_manifest_summary(tmp_path: Path) -> None:
    service = _service(tmp_path)
    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="my",
        style_preset="natural_human",
    )

    updated = service.submit_feedback(
        job_id=job.job_id,
        naturalness_score=5,
        translation_score=4,
        speed_score=5,
        voice_fit_score=4,
        usable_for_publish="needs_edit",
        failure_reason="pronunciation_issue",
        comment="Needs one pronunciation pass.",
    )

    paths = service.storage.paths_for(job.job_id)
    feedback = json.loads(paths.feedback.read_text(encoding="utf-8"))
    assert feedback["usable_for_publish"] == "needs_edit"
    assert feedback["failure_reason"] == "pronunciation_issue"
    assert updated.operator_feedback == feedback


def test_feedback_rejects_scores_outside_one_to_five(tmp_path: Path) -> None:
    service = _service(tmp_path)
    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="vi",
        style_preset="natural_human",
    )

    with pytest.raises(VoiceToolError) as exc:
        service.submit_feedback(
            job_id=job.job_id,
            naturalness_score=6,
            translation_score=4,
            speed_score=5,
            voice_fit_score=4,
            usable_for_publish="yes",
        )

    assert exc.value.code == "invalid_feedback"


def test_speech_rewrite_is_separate_stage_and_templates_are_distinct(tmp_path: Path) -> None:
    client = FakeTranslateClient()
    service = _service(tmp_path, client)

    variants = service.generate_style_variants(
        translated_text="တည်ငြိမ်သော ဘာသာပြန်စာသား။",
        target_language="my",
        voice_mode="humanized",
    )

    assert set(variants) == {"natural", "professional", "engaging"}
    assert len(set(variants.values())) == 3
    hints = [request.target_lang for request in client.requests]
    assert any("expression_style=natural" in hint for hint in hints)
    assert any("expression_style=engaging" in hint for hint in hints)
    assert any("Natural local human host delivery" in hint for hint in hints)
    assert any("Engaging local host delivery" in hint for hint in hints)


def test_voice_mode_is_closed_enum(tmp_path: Path) -> None:
    service = _service(tmp_path)

    with pytest.raises(VoiceToolError) as exc:
        service.rewrite_speech_text(
            translated_text="xin chao",
            target_language="vi",
            expression_style="natural",
            voice_mode="experimental",
        )

    assert exc.value.code == "invalid_choice"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("speaker_gender", {"speaker_gender": "neutral"}),
        ("expression_style", {"expression_style": "news"}),
        ("usage_scene", {"usage_scene": "livestream"}),
    ],
)
def test_humanized_host_controls_are_closed_enums(
    tmp_path: Path, field_name: str, kwargs: dict[str, str]
) -> None:
    service = _service(tmp_path)

    with pytest.raises(VoiceToolError) as exc:
        service.rewrite_speech_text(
            translated_text="xin chao",
            target_language="vi",
            **kwargs,
        )

    assert exc.value.code == "invalid_choice"
    assert field_name in str(exc.value)


def test_custom_humanize_prompt_persists_only_in_manifest(tmp_path: Path) -> None:
    client = FakeTranslateClient()
    service = _service(tmp_path, client)

    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="vi",
        speaker_gender="male",
        expression_style="engaging",
        usage_scene="product_intro",
        custom_humanize_prompt="更像本地真人主播，减少机器感。",
    )

    paths = service.storage.paths_for(job.job_id)
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    assert manifest["speaker_gender"] == "male"
    assert manifest["expression_style"] == "engaging"
    assert manifest["usage_scene"] == "product_intro"
    assert manifest["custom_humanize_prompt"] == "更像本地真人主播，减少机器感。"
    assert manifest["humanized_strategy_backend_only"] == "gemini_rewrite_plus_tts"
    public = service.storage.public_job_payload(job)
    assert public["speaker_gender"] == "male"
    assert public["expression_style"] == "engaging"
    assert public["usage_scene"] == "product_intro"
    assert "custom_humanize_prompt" not in public
    assert "humanized_strategy_backend_only" not in public
    assert "model" not in json.dumps(public).lower()


def test_public_voice_options_deduplicate_identical_backend_voice(tmp_path: Path) -> None:
    settings = _settings()
    settings.azure_tts_voice_map = {
        "mm_female_1": "my-MM-NilarNeural",
        "mm_male_1": "my-MM-NilarNeural",
    }
    service = VoiceToolService(
        storage=VoiceToolStorage(tmp_path / "artifacts" / "voice_tool"),
        translate_client=FakeTranslateClient(),
        settings_obj=settings,
        tts_func=fake_tts,
    )

    options = service.public_options("my")["voice_options"]

    assert options == [{"value": "female", "label": "女主播"}]


def test_public_payload_and_ui_do_not_expose_provider_vendor_model(tmp_path: Path) -> None:
    service = _service(tmp_path)
    job = service.translate(
        source_text="hello",
        source_language="en",
        target_language="vi",
        style_preset="news",
    )

    public_text = json.dumps(service.storage.public_job_payload(job), ensure_ascii=False)
    template = Path("gateway/app/templates/voice_tool.html").read_text(encoding="utf-8")

    for token in ("provider_used_backend_only", "gemini", "azure", "vendor", "model"):
        assert token not in public_text.lower()
        assert token not in template.lower()


@pytest.mark.parametrize(
    ("target_language", "source_text"),
    [
        ("my", "今天介绍一款适合日常使用的产品。"),
        ("vi", "Today we introduce a product for daily use."),
    ],
)
def test_generate_sample_jobs_for_burmese_and_vietnamese(
    tmp_path: Path, target_language: str, source_text: str
) -> None:
    service = _service(tmp_path)

    job = asyncio.run(
        service.generate(
            source_text=source_text,
            source_language="zh" if target_language == "my" else "en",
            target_language=target_language,
            style_preset="natural_human",
            voice_preset="natural",
            speed="normal",
        )
    )

    paths = service.storage.paths_for(job.job_id)
    assert paths.manifest.exists()
    assert paths.output_mp3.exists()
    assert job.target_language == target_language

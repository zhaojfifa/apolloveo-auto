from __future__ import annotations

import json
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from gateway.app.services.providers.gemini import GeminiTextTranslateResult
from gateway.app.services.voice_tool import VoiceToolError, VoiceToolService
from gateway.app.services.voice_tool.storage import VoiceToolStorage


class FakeTranslateClient:
    def __init__(self) -> None:
        self.requests = []

    def translate_segments(self, request):
        self.requests.append(request)
        return GeminiTextTranslateResult(translated={1: "မင်္ဂလာပါ။ သဘာဝကျကျ ပြောပါ။"})


async def fake_tts(text, voice, output_path, **kwargs):
    Path(output_path).write_bytes(b"fake-mp3-audio")


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
    assert manifest["provider_used_backend_only"] == {"translation": "gemini"}
    assert "provider_used_backend_only" not in service.storage.public_job_payload(job)
    assert "Burmese" in client.requests[0].target_lang


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
        "tts": "azure_speech",
    }
    public = service.storage.public_job_payload(updated)
    assert public["download_mp3_url"] == f"/api/voice-tool/download/{job.job_id}?format=mp3"
    assert "provider_used_backend_only" not in public


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

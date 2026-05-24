from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_LANGUAGES = frozenset({"zh", "en", "my", "vi"})
TARGET_LANGUAGES = frozenset({"my", "vi"})
STYLE_PRESETS = frozenset({"natural_human", "sales", "explainer", "news", "calm"})
VOICE_PRESETS = frozenset({"male", "female", "natural"})
VOICE_MODES = frozenset({"stable", "humanized"})
SPEED_PRESETS = frozenset({"slow", "normal", "fast"})
USABLE_FOR_PUBLISH_VALUES = frozenset({"yes", "needs_edit", "no"})
FAILURE_REASONS = frozenset(
    {
        "translation_wrong",
        "unnatural_voice",
        "speed_wrong",
        "pronunciation_issue",
        "audio_error",
        "other",
    }
)


LANGUAGE_NAMES = {
    "zh": "Chinese",
    "en": "English",
    "my": "Burmese",
    "vi": "Vietnamese",
}


@dataclass(frozen=True)
class VoiceToolFeedback:
    naturalness_score: int
    translation_score: int
    speed_score: int
    voice_fit_score: int
    usable_for_publish: str
    failure_reason: str | None = None
    comment: str = ""
    submitted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "naturalness_score": self.naturalness_score,
            "translation_score": self.translation_score,
            "speed_score": self.speed_score,
            "voice_fit_score": self.voice_fit_score,
            "usable_for_publish": self.usable_for_publish,
            "failure_reason": self.failure_reason,
            "comment": self.comment,
            "submitted_at": self.submitted_at,
        }


@dataclass
class VoiceToolJob:
    job_id: str
    source_text: str
    source_language: str
    target_language: str
    translated_text: str = ""
    speech_text: str = ""
    style_preset: str = "natural_human"
    voice_preset: str = "natural"
    voice_mode: str = "stable"
    speed: str = "normal"
    speech_variants: dict[str, str] = field(default_factory=dict)
    provider_used_backend_only: dict[str, str] = field(default_factory=dict)
    audio_path: str | None = None
    manifest_path: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    operator_feedback: dict[str, Any] | None = None

    def as_manifest(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_text": self.source_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "translated_text": self.translated_text,
            "speech_text": self.speech_text,
            "style_preset": self.style_preset,
            "voice_preset": self.voice_preset,
            "voice_mode": self.voice_mode,
            "speed": self.speed,
            "speech_variants": dict(self.speech_variants),
            "provider_used_backend_only": dict(self.provider_used_backend_only),
            "audio_path": self.audio_path,
            "manifest_path": self.manifest_path,
            "created_at": self.created_at,
            "operator_feedback": self.operator_feedback,
        }

    @classmethod
    def from_manifest(cls, payload: dict[str, Any]) -> "VoiceToolJob":
        return cls(
            job_id=str(payload.get("job_id") or ""),
            source_text=str(payload.get("source_text") or ""),
            source_language=str(payload.get("source_language") or ""),
            target_language=str(payload.get("target_language") or ""),
            translated_text=str(payload.get("translated_text") or ""),
            speech_text=str(payload.get("speech_text") or ""),
            style_preset=str(payload.get("style_preset") or "natural_human"),
            voice_preset=str(payload.get("voice_preset") or "natural"),
            voice_mode=str(payload.get("voice_mode") or "stable"),
            speed=str(payload.get("speed") or "normal"),
            speech_variants=dict(payload.get("speech_variants") or {}),
            provider_used_backend_only=dict(payload.get("provider_used_backend_only") or {}),
            audio_path=str(payload.get("audio_path") or "") or None,
            manifest_path=str(payload.get("manifest_path") or "") or None,
            created_at=str(payload.get("created_at") or ""),
            operator_feedback=(
                dict(payload.get("operator_feedback"))
                if isinstance(payload.get("operator_feedback"), dict)
                else None
            ),
        )


@dataclass(frozen=True)
class VoiceToolPaths:
    root: Path
    source: Path
    translated: Path
    speech_text: Path
    output_mp3: Path
    output_wav: Path
    manifest: Path
    feedback: Path

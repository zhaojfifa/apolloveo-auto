from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import VoiceToolFeedback, VoiceToolJob, VoiceToolPaths

_JOB_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


class VoiceToolStorage:
    def __init__(self, artifact_root: Path | str) -> None:
        self.artifact_root = Path(artifact_root).expanduser().resolve()

    def paths_for(self, job_id: str) -> VoiceToolPaths:
        if not _JOB_ID_RE.match(str(job_id or "")):
            raise ValueError("invalid job_id")
        root = self.artifact_root / job_id
        return VoiceToolPaths(
            root=root,
            source=root / "source.txt",
            translated=root / "translated.txt",
            speech_text=root / "speech_text.txt",
            output_mp3=root / "output.mp3",
            output_wav=root / "output.wav",
            manifest=root / "manifest.json",
            feedback=root / "feedback.json",
        )

    def write_job(self, job: VoiceToolJob) -> VoiceToolJob:
        paths = self.paths_for(job.job_id)
        paths.root.mkdir(parents=True, exist_ok=True)
        paths.source.write_text(job.source_text, encoding="utf-8")
        paths.translated.write_text(job.translated_text, encoding="utf-8")
        paths.speech_text.write_text(job.speech_text, encoding="utf-8")
        job.manifest_path = str(paths.manifest)
        payload = job.as_manifest()
        paths.manifest.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return job

    def read_job(self, job_id: str) -> VoiceToolJob:
        paths = self.paths_for(job_id)
        if not paths.manifest.exists():
            raise FileNotFoundError("voice tool job not found")
        payload = json.loads(paths.manifest.read_text(encoding="utf-8"))
        return VoiceToolJob.from_manifest(payload)

    def write_feedback(
        self, job: VoiceToolJob, feedback: VoiceToolFeedback
    ) -> VoiceToolJob:
        paths = self.paths_for(job.job_id)
        paths.root.mkdir(parents=True, exist_ok=True)
        data = feedback.as_dict()
        paths.feedback.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        job.operator_feedback = data
        self.write_job(job)
        return job

    def public_job_payload(self, job: VoiceToolJob) -> dict[str, Any]:
        paths = self.paths_for(job.job_id)
        return {
            "job_id": job.job_id,
            "source_text": job.source_text,
            "source_language": job.source_language,
            "target_language": job.target_language,
            "translated_text": job.translated_text,
            "speech_text": job.speech_text,
            "style_preset": job.style_preset,
            "voice_preset": job.voice_preset,
            "voice_mode": job.voice_mode,
            "speed": job.speed,
            "speech_variants": dict(job.speech_variants),
            "audio_ready": bool(job.audio_path and Path(job.audio_path).exists()),
            "audio_url": f"/api/voice-tool/download/{job.job_id}" if job.audio_path else None,
            "download_mp3_url": (
                f"/api/voice-tool/download/{job.job_id}?format=mp3"
                if paths.output_mp3.exists()
                else None
            ),
            "download_wav_url": (
                f"/api/voice-tool/download/{job.job_id}?format=wav"
                if paths.output_wav.exists()
                else None
            ),
            "created_at": job.created_at,
            "operator_feedback": job.operator_feedback,
        }

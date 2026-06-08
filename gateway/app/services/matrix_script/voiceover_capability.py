"""Matrix Script voiceover capability — real TTS narration with honest status.

Produces REAL narration audio through the existing TTS paths already in the repo —
keyless ``edge_tts`` and credentialed Azure Speech — and reports an operator-safe
status. It NEVER fabricates audio: when no TTS path succeeds the caller keeps the
silent fallback and the status reports the honest block reason.

Resolution order (first success wins):
1. **Azure Speech** — only when ``AZURE_SPEECH_KEY`` + ``AZURE_SPEECH_REGION`` are
   present in the environment (credentialed path).
2. **edge_tts** — keyless fallback (no credential required).

Status semantics (operator-safe; the Owner's heavy-batch vocabulary):
- ``generated`` — a real audio file was produced by a TTS provider.
- ``blocked_credential_missing`` — no credentialed TTS provider is configured AND
  the keyless fallback did not produce audio (the primary block is missing config).
- ``blocked_provider_fail`` — a credentialed provider WAS configured but the call
  failed, and the keyless fallback also failed.

Hard boundary: no secret is read into any artifact/manifest/log here — only the
boolean presence of credentials gates the attempt; the key/region values are passed
straight to the provider call and never returned, logged, or stored.
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, Optional

STATUS_GENERATED = "generated"
STATUS_BLOCKED_CREDENTIAL_MISSING = "blocked_credential_missing"
STATUS_BLOCKED_PROVIDER_FAIL = "blocked_provider_fail"

PROVIDER_AZURE = "azure_tts"
PROVIDER_EDGE = "edge_tts"
PROVIDER_NONE = "none"

_AZURE_KEY_ENV = "AZURE_SPEECH_KEY"
_AZURE_REGION_ENV = "AZURE_SPEECH_REGION"
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# Operator-safe labels (no provider/vendor brand leaked into primary UI copy).
_OPERATOR_LABEL = {
    STATUS_GENERATED: "旁白已生成",
    STATUS_BLOCKED_CREDENTIAL_MISSING: "旁白未生成 · 缺少语音凭证（已保留静音）",
    STATUS_BLOCKED_PROVIDER_FAIL: "旁白未生成 · 语音服务暂不可用（已保留静音）",
}

# Injectable async synth callables (real providers by default; fakes in tests).
AzureSynth = Callable[..., Awaitable[None]]   # (text, voice, out, *, speech_key, speech_region)
EdgeSynth = Callable[[str, str, str], Awaitable[None]]  # (text, voice, out)


@dataclass(frozen=True)
class VoiceoverOutcome:
    """Result of a narration attempt — audio path (when produced) + honest status."""

    status: str
    provider: str
    audio_path: Optional[str] = None
    detail: str = ""

    @property
    def generated(self) -> bool:
        return self.status == STATUS_GENERATED

    @property
    def operator_label_zh(self) -> str:
        return _OPERATOR_LABEL.get(self.status, "旁白状态未知")

    def to_status_dict(self) -> dict:
        """Operator-safe capability-status dict (no secret, no raw provider field leak)."""
        return {
            "capability": "voiceover",
            "status": self.status,
            "generated": self.generated,
            "operator_label_zh": self.operator_label_zh,
        }


def azure_credentials_present(env: Optional[Mapping[str, str]] = None) -> bool:
    src = env if env is not None else os.environ
    return bool((src.get(_AZURE_KEY_ENV) or "").strip()) and bool(
        (src.get(_AZURE_REGION_ENV) or "").strip()
    )


def _run(coro: Awaitable[None]) -> None:
    asyncio.run(coro)


def _default_azure_synth() -> AzureSynth:
    from gateway.app.providers.azure_speech import generate_audio_azure_speech

    return generate_audio_azure_speech


def _default_edge_synth() -> EdgeSynth:
    from gateway.app.providers.edge_tts import generate_audio_edge_tts

    return generate_audio_edge_tts


def _produced(path: str) -> bool:
    return bool(path) and os.path.exists(path) and os.path.getsize(path) > 0


def synthesize_narration(
    text: str,
    out_path: str,
    *,
    env: Optional[Mapping[str, str]] = None,
    voice: str = DEFAULT_VOICE,
    azure_synth: Optional[AzureSynth] = None,
    edge_synth: Optional[EdgeSynth] = None,
) -> VoiceoverOutcome:
    """Synthesize a single narration track; return the produced audio + honest status.

    ``azure_synth`` / ``edge_synth`` are injectable async callables (the real providers
    by default) so the compose path is unit-testable without any network or secret.
    """
    if not isinstance(text, str) or not text.strip():
        return VoiceoverOutcome(
            STATUS_BLOCKED_PROVIDER_FAIL, PROVIDER_NONE, None, "empty narration text"
        )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    src = env if env is not None else os.environ
    azure_ready = azure_credentials_present(src)
    azure_synth = azure_synth or _default_azure_synth()
    edge_synth = edge_synth or _default_edge_synth()

    errors: list = []

    # 1. Credentialed provider (Azure) — only when configured.
    if azure_ready:
        try:
            _run(
                azure_synth(
                    text.strip(),
                    voice,
                    out_path,
                    speech_key=(src.get(_AZURE_KEY_ENV) or "").strip(),
                    speech_region=(src.get(_AZURE_REGION_ENV) or "").strip(),
                )
            )
            if _produced(out_path):
                return VoiceoverOutcome(STATUS_GENERATED, PROVIDER_AZURE, out_path)
            errors.append("azure produced no audio")
        except Exception as exc:  # noqa: BLE001 — provider failure is a status, not a crash
            errors.append(f"azure: {exc.__class__.__name__}")

    # 2. Keyless fallback (edge_tts).
    try:
        _run(edge_synth(text.strip(), voice, out_path))
        if _produced(out_path):
            return VoiceoverOutcome(STATUS_GENERATED, PROVIDER_EDGE, out_path)
        errors.append("edge produced no audio")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"edge: {exc.__class__.__name__}")

    detail = "; ".join(errors)[:200]
    if not azure_ready:
        # No credentialed provider configured → the primary block is missing config.
        return VoiceoverOutcome(
            STATUS_BLOCKED_CREDENTIAL_MISSING, PROVIDER_NONE, None, detail
        )
    return VoiceoverOutcome(STATUS_BLOCKED_PROVIDER_FAIL, PROVIDER_NONE, None, detail)

"""Matrix Script real operator trial orchestrator (PR-17R).

The Real Operator Trial Wave closure: chains the gate → an optional Akool
one-shot attempt → the local minimal-result loop (real final.mp4) → artifact
staging → a Delivery staged-candidate block.

Behavior by gate state:
- gate OFF (default): no provider attempt; fallback scenes; final.mp4; staged.
- gate ON but not wired / no key: operator-readable blocked reason; fallback;
  final.mp4; staged.
- gate ON + key + injected transport: one shot attempted; the provider output
  is accepted only internally (never surfaced as a URL); the staged final.mp4
  is the assembled local pack; the attempt is recorded with a provider-AGNOSTIC
  label ``real_oneshot_attempted``.

Hard boundary: ``official_publish_ready=false``; no ``publish_url`` /
``publish_status`` / ``download_url`` / ``provider_url`` / ``temporary_url`` /
Akool task id / model / credit / raw provider response in the returned payload;
provider temporary URL is never used as ``final_video``. Real generation
remains gated (Capability Expansion W2.3) — enabling it is an explicit operator
act. ffmpeg absence raises (never a fake final.mp4).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterInvocation,
)
from gateway.app.services.matrix_script.akool_real_gate import (
    evaluate_akool_real_gate,
    guarded_generate_one_shot,
)
from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    stage_minimal_result,
)
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    GENERATION_PROVIDER_NONE,
    GENERATION_PROVIDER_REAL_ONESHOT,
    staged_record_to_delivery_block,
)
from gateway.app.services.matrix_script.minimal_result_loop import run_minimal_result_loop
from gateway.app.services.matrix_script.minimal_result_service import (
    derive_outline_from_task,
)

LINE_ID = "matrix_script"


class RealTrialError(ValueError):
    """Raised on an invalid real-trial input."""


@dataclass(frozen=True)
class MatrixScriptRealTrialResult:
    task_id: Optional[str]
    gate_enabled: bool
    real_oneshot_used: bool
    generation_provider: str
    delivery_block: Mapping[str, Any]
    blocked_reason_zh: Optional[str] = None
    line_id: str = LINE_ID
    official_publish_ready: bool = False


def _task_id(task: Mapping[str, Any]) -> Optional[str]:
    for key in ("task_id", "id"):
        v = task.get(key)
        if isinstance(v, str) and v:
            return v
    config = task.get("config")
    if isinstance(config, Mapping):
        entry = config.get("entry")
        if isinstance(entry, Mapping):
            v = entry.get("task_id")
            if isinstance(v, str) and v:
                return v
    return None


def run_matrix_script_real_trial(
    task: Mapping[str, Any],
    output_dir: "str | os.PathLike[str]",
    *,
    sink: Any,
    env: Optional[Mapping[str, str]] = None,
    resolver: Any = None,
    akool_credentials: Optional[AdapterCredentials] = None,
    akool_transport: Optional[Callable[..., Any]] = None,
    aspect_ratio: str = "9:16",
    target_duration_seconds: float = 20.0,
) -> MatrixScriptRealTrialResult:
    """Run the real operator trial; return a staged delivery candidate."""
    if not isinstance(task, Mapping):
        raise RealTrialError("task must be a mapping")
    if sink is None or not hasattr(sink, "put"):
        raise RealTrialError("sink must provide a put(local_path, artifact_name) method")

    task_id = _task_id(task)

    # 1. Gate + optional one-shot attempt (no media spliced from provider; the
    #    skeleton adapter yields no local clip — the attempt is recorded only).
    gate = evaluate_akool_real_gate(env=env, resolver=resolver)
    real_used = False
    blocked_reason: Optional[str] = None
    if gate.enabled:
        guarded = guarded_generate_one_shot(
            gate=gate,
            invocation=AdapterInvocation(
                capability_kind="video_gen",
                inputs={"image_url": "scene-1", "prompt": "shot-1"},
            ),
            credentials=akool_credentials,
            transport=akool_transport,
        )
        real_used = guarded.used_real_provider
        if not real_used:
            blocked_reason = guarded.blocked_reason_zh or guarded.operator_reason_zh
    else:
        blocked_reason = gate.operator_reason_zh

    # 2. Local pack (real final.mp4). Raises FFmpegUnavailableError if ffmpeg
    #    is missing — a fake final.mp4 is never produced.
    outline = derive_outline_from_task(task)
    loop = run_minimal_result_loop(
        outline,
        os.fspath(output_dir),
        task_id=task_id,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
    )

    # 3. Stage the pack into artifact_staged refs.
    record = stage_minimal_result(
        sink=sink,
        task_id=task_id,
        final_video_path=loop.final_video_path,
        manifest_path=loop.manifest_path,
        subtitles_path=loop.subtitle_path,
        audio_path=loop.audio_path,
        scene_clip_paths=loop.scene_clip_paths,
    )

    # 4. Delivery staged-candidate block (provider-agnostic label).
    provider_label = GENERATION_PROVIDER_REAL_ONESHOT if real_used else GENERATION_PROVIDER_NONE
    delivery_block = staged_record_to_delivery_block(record, generation_provider=provider_label)

    return MatrixScriptRealTrialResult(
        task_id=task_id,
        gate_enabled=gate.enabled,
        real_oneshot_used=real_used,
        generation_provider=provider_label,
        delivery_block=delivery_block,
        blocked_reason_zh=blocked_reason,
    )


def real_trial_result_to_payload(result: MatrixScriptRealTrialResult) -> Dict[str, object]:
    """Operator-safe JSON payload for the route (delivery block + trial meta)."""
    payload: Dict[str, object] = dict(result.delivery_block)
    payload["task_id"] = result.task_id
    payload["gate_enabled"] = result.gate_enabled
    payload["real_oneshot_used"] = result.real_oneshot_used
    payload["generation_provider"] = result.generation_provider
    payload["official_publish_ready"] = result.official_publish_ready
    if result.blocked_reason_zh:
        payload["blocked_reason_zh"] = result.blocked_reason_zh
    return payload

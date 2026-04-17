from __future__ import annotations

from typing import Any

from gateway.app.utils.pipeline_config import parse_pipeline_config


def normalize_source_audio_policy(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"keep", "preserve", "preserve_original", "keep_original", "original"}:
        return "preserve"
    return "mute"


def source_audio_policy_from_task(task: dict | None) -> str:
    task_obj = task if isinstance(task, dict) else {}
    config = dict(task_obj.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    pipeline_config = parse_pipeline_config(task_obj.get("pipeline_config"))
    return normalize_source_audio_policy(
        config.get("source_audio_policy")
        or pipeline_config.get("source_audio_policy")
        or bgm.get("strategy")
        or pipeline_config.get("bgm_strategy")
        or pipeline_config.get("audio_strategy")
    )

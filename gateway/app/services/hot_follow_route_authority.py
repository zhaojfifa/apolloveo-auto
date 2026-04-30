from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from gateway.app.services.source_audio_policy import normalize_source_audio_policy
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage


HOT_FOLLOW_ROUTE_OWNER = "hot_follow_route_decision_v1"
SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW = "switch_local_preserve_to_tts_subtitle_flow"


def materialize_local_tts_subtitle_route_action(
    repo: Any,
    task_id: str,
    task: dict[str, Any],
    *,
    reason: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Formal route-stage action from local preserve-source testing to TTS flow.

    This owns route policy only. It does not write subtitle truth; Subtitle Stage
    remains the only owner of target subtitle materialization/currentness.
    """
    current = dict(task or {})
    if str(current.get("kind") or current.get("category_key") or "").strip().lower() != "hot_follow":
        raise ValueError("task is not hot_follow")
    if str(current.get("source_type") or "").strip().lower() != "local" and str(current.get("platform") or "").strip().lower() != "local":
        raise ValueError("task is not local upload")

    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    config = dict(current.get("config") or {})
    config["source_audio_policy"] = normalize_source_audio_policy("mute")
    bgm = dict(config.get("bgm") or {})
    if bgm:
        bgm["strategy"] = "replace"
        config["bgm"] = bgm

    pipeline_config = parse_pipeline_config(current.get("pipeline_config"))
    pipeline_config["source_audio_policy"] = "mute"
    pipeline_config["bgm_strategy"] = "replace"
    pipeline_config["audio_strategy"] = "mute"

    updates = {
        "config": config,
        "pipeline_config": pipeline_config_to_storage(pipeline_config),
        "hot_follow_route_decision_owner": HOT_FOLLOW_ROUTE_OWNER,
        "hot_follow_route_stage_action": SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW,
        "hot_follow_route_stage_action_at": timestamp,
        "hot_follow_route_stage_action_reason": str(reason or "operator_selected_subtitle_dub_flow").strip(),
        "hot_follow_route_target": "tts_replace_route",
        "dub_status": "pending" if str(current.get("dub_status") or "").strip().lower() in {"skipped", "done", "ready"} else current.get("dub_status"),
        "compose_status": "pending" if str(current.get("compose_status") or "").strip().lower() in {"done", "ready"} else current.get("compose_status"),
        "final_fresh": False,
        "final_stale_reason": "route_changed_to_tts_subtitle_flow",
    }
    updates = {key: value for key, value in updates.items() if value is not None}
    return policy_upsert(
        repo,
        task_id,
        current,
        updates,
        step="hot_follow_route_stage.switch_to_tts_subtitle_flow",
    )

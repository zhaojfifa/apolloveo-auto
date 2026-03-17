from __future__ import annotations

from typing import Any, Dict


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _pick_final(task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    final = _as_dict(state.get("final")) or _as_dict(task.get("final"))
    if bool(final.get("exists")):
        return final

    for d in _as_list(state.get("deliverables")):
        if not isinstance(d, dict):
            continue
        if str(d.get("kind") or "").strip().lower() == "final":
            if str(d.get("status") or d.get("state") or "").strip().lower() == "done" or d.get("url"):
                return {
                    "exists": True,
                    "key": d.get("key"),
                    "url": d.get("url"),
                    "content_type": "video/mp4",
                }

    deliverables = _as_dict(state.get("deliverables"))
    final_item = _as_dict(deliverables.get("final_mp4"))
    if final_item.get("url"):
        return {
            "exists": True,
            "key": final_item.get("key"),
            "url": final_item.get("url"),
            "content_type": "video/mp4",
        }

    return {"exists": False}


def _resolve_final_url(task_id: str, task: Dict[str, Any], state: Dict[str, Any], final: Dict[str, Any]) -> tuple[str | None, bool]:
    deliverables = state.get("deliverables")
    evidence = bool(final.get("exists"))
    url = None
    if isinstance(deliverables, dict):
        url = _as_dict(deliverables.get("final_mp4")).get("url")
        evidence = evidence or bool(_as_dict(deliverables.get("final_mp4")))
    if not url:
        for d in _as_list(deliverables):
            if not isinstance(d, dict):
                continue
            if str(d.get("kind") or "").strip().lower() == "final":
                evidence = evidence or str(d.get("status") or d.get("state") or "").strip().lower() == "done" or bool(d.get("key"))
                if d.get("url"):
                    url = d.get("url")
                    break
    media = _as_dict(state.get("media")) or _as_dict(task.get("media"))
    extra = _as_dict(state.get("extra")) or _as_dict(task.get("extra"))
    url = (
        url
        or media.get("final_url")
        or media.get("final_video_url")
        or extra.get("final_video_url")
        or state.get("final_url")
        or state.get("final_video_url")
        or final.get("url")
        or None
    )
    if url:
        return str(url), True
    compose = _as_dict(state.get("compose"))
    compose_last = _as_dict(compose.get("last"))
    compose_status = str(compose_last.get("status") or state.get("compose_status") or task.get("compose_status") or "").strip().lower()
    evidence = evidence or compose_status in {"done", "ready", "success", "completed"}
    if evidence and task_id:
        return f"/v1/tasks/{task_id}/final", True
    return None, evidence


def compute_hot_follow_state(task: Dict[str, Any], base_state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    # Operational policy for Hot Follow v1.9:
    # 1. execution state = runtime step result
    # 2. artifact truth = actual current generated outputs
    # 3. operational readiness = operator-facing readiness derived from artifacts
    # 4. legacy/status summary fields are compatibility-only, not the source of truth
    state: Dict[str, Any] = dict(base_state or {})
    task_id = str(state.get("task_id") or task.get("task_id") or task.get("id") or "")

    state.setdefault("task_id", task_id)
    state.setdefault("kind", task.get("kind", "hot_follow"))

    final = _pick_final(task, state)
    final_url, final_evidence = _resolve_final_url(task_id, task, state, final)
    final_exists = bool(final.get("exists") or final_evidence)
    if final_exists and not final_url and task_id:
        final_url = f"/v1/tasks/{task_id}/final"

    final_out = dict(final)
    final_out["exists"] = final_exists
    if final_url and not final_out.get("url"):
        final_out["url"] = final_url
    state["final"] = final_out

    media = dict(_as_dict(state.get("media")))
    media["final_url"] = final_url
    media["final_video_url"] = final_url
    state["media"] = media
    state["final_url"] = final_url
    state["final_video_url"] = final_url

    if isinstance(state.get("deliverables"), dict):
        deliverables = dict(state.get("deliverables") or {})
        final_item = dict(_as_dict(deliverables.get("final_mp4")) or {"label": "final.mp4"})
        final_item["url"] = final_url
        deliverables["final_mp4"] = final_item
        state["deliverables"] = deliverables
    elif isinstance(state.get("deliverables"), list):
        patched = []
        seen_final = False
        for item in state.get("deliverables") or []:
            if not isinstance(item, dict):
                patched.append(item)
                continue
            row = dict(item)
            if str(row.get("kind") or "").strip().lower() == "final":
                row["url"] = final_url
                if final_exists:
                    row["status"] = "done"
                    row["state"] = "done"
                seen_final = True
            patched.append(row)
        if not seen_final:
            patched.append(
                {
                    "kind": "final",
                    "title": "Final Video",
                    "label": "Final Video",
                    "key": None,
                    "url": final_url,
                    "status": "done" if final_exists else "pending",
                    "state": "done" if final_exists else "pending",
                    "size": None,
                    "sha256": None,
                }
            )
        state["deliverables"] = patched

    audio = _as_dict(state.get("audio"))
    subtitles = _as_dict(state.get("subtitles"))
    audio_status = str(
        audio.get("status")
        or task.get("dub_status")
        or ""
    ).strip().lower()
    audio_done = audio_status in {"done", "ready", "success", "completed"}
    voiceover_exists = bool(
        audio.get("voiceover_url")
        or _as_dict(state.get("media")).get("voiceover_url")
        or task.get("mm_audio_key")
        or task.get("mm_audio_path")
    )
    tts_voice = str(audio.get("tts_voice") or task.get("voice_id") or "").strip()
    tts_voice_valid = bool(tts_voice and tts_voice not in {"-", "none", "null"})
    audio_ready_hint = audio.get("audio_ready")
    if audio_ready_hint is None:
        audio_ready = bool(audio_done and voiceover_exists and tts_voice_valid)
    else:
        audio_ready = bool(audio_ready_hint)
    subtitle_ready_hint = subtitles.get("subtitle_ready")
    subtitle_artifact_exists = bool(
        subtitles.get("subtitle_artifact_exists")
        or subtitles.get("actual_burn_subtitle_source")
        or subtitles.get("edited_text")
        or subtitles.get("srt_text")
        or task.get("mm_srt_path")
        or task.get("origin_srt_path")
    )
    subtitle_ready = bool(subtitle_artifact_exists) if subtitle_ready_hint is None else bool(subtitle_ready_hint)
    subtitle_ready_reason = str(subtitles.get("subtitle_ready_reason") or ("ready" if subtitle_ready else "subtitle_missing"))
    no_dub = bool(audio.get("no_dub"))
    no_dub_reason = str(audio.get("no_dub_reason") or "").strip() or None
    if voiceover_exists or audio_ready:
        no_dub = False
        no_dub_reason = None
    compose_ready = bool(final_exists and (audio_ready or no_dub))

    compose = dict(_as_dict(state.get("compose")))
    last = dict(_as_dict(compose.get("last")))
    if compose_ready:
        last["status"] = "done"
        last["error"] = None
        state["compose_status"] = "done"
    elif last:
        last["status"] = "pending"
    if last:
        compose["last"] = last
    state["compose"] = compose

    pipeline = list(_as_list(state.get("pipeline")))
    if compose_ready and pipeline:
        for step in pipeline:
            if not isinstance(step, dict):
                continue
            if str(step.get("key") or "").strip().lower() == "compose":
                step["status"] = "done"
                step["state"] = "done"
                step["error"] = None
                step["message"] = step.get("message") or "final video merge"
    elif pipeline:
        for step in pipeline:
            if not isinstance(step, dict):
                continue
            if str(step.get("key") or "").strip().lower() == "compose":
                step["status"] = "pending"
                step["state"] = "pending"
    state["pipeline"] = pipeline

    blocking: list[str] = []
    if not compose_ready:
        blocking.append("compose_not_done")
        if not subtitle_ready:
            blocking.append("subtitle_not_ready")
        if not audio_done and not no_dub:
            blocking.append("audio_not_done")
        if not voiceover_exists and not no_dub:
            blocking.append("voiceover_missing")
        if not tts_voice_valid and not no_dub:
            blocking.append("tts_voice_invalid")
        if final_exists and not audio_ready and not no_dub:
            blocking.append("audio_not_ready")
        # Only surface no_dub_reason as a blocker when subtitle is also not ready;
        # once subtitles are ready the no_speech signal is informational only.
        if no_dub and no_dub_reason and not subtitle_ready:
            blocking.append(no_dub_reason)
    else:
        blocking = [b for b in blocking if b != "compose_not_done"]

    state["composed_ready"] = compose_ready
    state["composed_reason"] = "ready" if compose_ready else "not_ready"
    if isinstance(state.get("deliverables"), list):
        for item in state.get("deliverables") or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("kind") or "").strip().lower() == "final":
                item["status"] = "done" if compose_ready else "pending"
                item["state"] = "done" if compose_ready else "pending"
                break
    # compose_reason: if no_dub but subtitle is already ready, use compose_not_done
    # so the compose button is enabled; only use no_dub_reason while subtitle is missing.
    _compose_reason: str
    if compose_ready:
        _compose_reason = "ready"
    elif no_dub and not subtitle_ready and no_dub_reason:
        _compose_reason = no_dub_reason
    else:
        _compose_reason = "compose_not_done"
    state["ready_gate"] = {
        "final_exists": final_exists,
        "subtitle_ready": subtitle_ready,
        "subtitle_ready_reason": subtitle_ready_reason,
        "audio_ready": audio_ready,
        "audio_ready_reason": str(audio.get("audio_ready_reason") or ("ready" if audio_ready else "audio_not_ready")),
        "compose_ready": compose_ready,
        "publish_ready": compose_ready,
        "compose_reason": _compose_reason,
        "blocking": blocking,
    }
    return state

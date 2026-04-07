from gateway.app.lines.base import LineRegistry
from gateway.app.services.skills_runtime import load_line_skills_bundle, run_loaded_skills_bundle


def _advisory_payload(
    *,
    task=None,
    ready_gate=None,
    artifact_facts=None,
    current_attempt=None,
    operator_summary=None,
):
    return {
        "task": task or {"task_id": "hf-skills-runtime", "kind": "hot_follow", "target_lang": "mm"},
        "line": {
            "line_id": "hot_follow_line",
            "skills_bundle_ref": "skills/hot_follow",
        },
        "ready_gate": ready_gate or {},
        "artifact_facts": artifact_facts or {},
        "current_attempt": current_attempt or {},
        "operator_summary": operator_summary or {},
        "pipeline": [],
        "pipeline_legacy": {},
        "deliverables": [],
        "media": {},
        "source_video": {},
    }


def test_hot_follow_skills_runtime_loader_resolves_live_bundle():
    line = LineRegistry.for_kind("hot_follow")

    bundle = load_line_skills_bundle(line)

    assert bundle is not None
    assert bundle.bundle_id == "hot_follow_skills_v1"
    assert bundle.line_id == "hot_follow_line"
    assert bundle.bundle_ref == "skills/hot_follow"
    assert bundle.hook_kind == "advisory"
    assert bundle.stage_order == ("input", "routing", "quality", "recovery")
    assert set(bundle.stage_runners) == {"input", "routing", "quality", "recovery"}


def test_hot_follow_skills_runtime_executes_bundle_stages_for_recompose_advisory():
    line = LineRegistry.for_kind("hot_follow")
    bundle = load_line_skills_bundle(line)

    execution = run_loaded_skills_bundle(
        bundle,
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": False,
                "publish_ready": False,
                "blocking": ["compose_not_done", "final_stale"],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "pending",
                "requires_recompose": True,
                "final_stale_reason": "final_stale_after_dub",
                "current_subtitle_source": "mm.srt",
            },
        ),
    )

    assert execution["bundle_ref"] == "skills/hot_follow"
    assert execution["stage_results"]["routing"]["decision_key"] == "recompose_required"
    assert execution["stage_results"]["recovery"] == {
        "id": "hf_advisory_recompose_required",
        "kind": "operator_guidance",
        "level": "warning",
        "recommended_next_action": "recompose_final",
        "operator_hint": "recompose recommended",
        "explanation": "当前字幕或配音已更新，建议重新合成最终视频以生成最新版本。",
        "evidence": {
            "final_exists": True,
            "compose_status": "pending",
            "final_stale_reason": "final_stale_after_dub",
            "blocking": ["compose_not_done", "final_stale"],
        },
    }

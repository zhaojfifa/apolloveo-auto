from pathlib import Path
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.deps import get_task_repository
from gateway.app.lines.base import LineRegistry
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.routers import tasks as tasks_router
from gateway.app.services import hot_follow_skills_advisory as skills_advisory


class _Repo:
    def __init__(self):
        self._rows = {}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        cur = dict(self._rows.get(task_id) or {})
        cur.update(fields or {})
        self._rows[task_id] = cur
        return cur


def _patch_workbench_dependencies(monkeypatch):
    monkeypatch.setattr(hf_router, "_scene_pack_info", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(hf_router, "_deliverable_url", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(hf_router, "_hf_persisted_audio_state", lambda *_args, **_kwargs: {"exists": False, "voiceover_url": None})
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "missing",
            "dub_current": False,
            "dub_current_reason": "missing",
            "resolved_voice": None,
            "actual_provider": None,
            "requested_voice": None,
        },
    )


def _advisory_payload(
    *,
    ready_gate=None,
    artifact_facts=None,
    current_attempt=None,
    operator_summary=None,
):
    return {
        "kind": "hot_follow",
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


def test_hot_follow_advisory_bundle_resolves_from_line_contract():
    line = LineRegistry.for_kind("hot_follow")

    bundle = skills_advisory.resolve_hot_follow_skills_bundle(line)

    assert bundle is not None
    assert bundle.bundle_id == "hot_follow_advisory_v0"
    assert bundle.bundle_ref == "docs/skills/"
    assert bundle.hook_kind == "advisory"


def test_hot_follow_advisory_v0_recommends_recompose_for_stale_final():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-recompose", "kind": "hot_follow"},
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
            operator_summary={"last_successful_output_available": True},
        ),
    )

    assert advisory == {
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


def test_hot_follow_advisory_v0_recommends_subtitle_review_when_missing():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-subtitle", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "audio_ready": False,
                "compose_ready": False,
                "publish_ready": False,
                "blocking": ["compose_not_done", "subtitle_not_ready"],
            },
            artifact_facts={
                "final_exists": False,
                "audio_exists": False,
                "subtitle_exists": False,
            },
            current_attempt={
                "audio_ready": False,
                "compose_status": "never",
                "requires_recompose": False,
            },
        ),
    )

    assert advisory == {
        "id": "hf_advisory_review_subtitles",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "review_subtitles",
        "operator_hint": "subtitle review recommended",
        "explanation": "当前主字幕还未准备完成，建议先检查并保存 mm.srt 后再继续后续链路。",
        "evidence": {
            "subtitle_ready": False,
            "subtitle_ready_reason": "subtitle_missing",
            "subtitle_exists": False,
        },
    }


def test_hot_follow_advisory_v0_recommends_continue_qa_when_final_is_ready():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-final-ready", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": True,
                "publish_ready": True,
                "blocking": [],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "done",
                "requires_recompose": False,
                "current_subtitle_source": "mm.srt",
            },
            operator_summary={"last_successful_output_available": True},
        ),
    )

    assert advisory == {
        "id": "hf_advisory_final_ready",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "continue_qa",
        "operator_hint": "no further action currently required",
        "explanation": "当前成片已可用，可继续做字幕、配音或成片 QA 复核。",
        "evidence": {
            "final_exists": True,
            "compose_ready": True,
            "publish_ready": True,
            "last_successful_output_available": True,
        },
    }


def test_hot_follow_advisory_v0_noops_for_non_hot_follow_kind():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "skills-noop-non-hf", "kind": "avatar"},
        _advisory_payload(
            ready_gate={"subtitle_ready": True},
            artifact_facts={"final_exists": True},
            current_attempt={"audio_ready": True},
        ),
    )

    assert advisory is None


def test_hot_follow_advisory_v0_safe_fallback_on_hook_failure(monkeypatch):
    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", lambda _input: (_ for _ in ()).throw(RuntimeError("boom")))

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-safe-fallback", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={"subtitle_ready": True},
            artifact_facts={"final_exists": True},
            current_attempt={"audio_ready": True},
        ),
    )

    assert advisory is None


def test_hot_follow_advisory_noop_preserves_workbench_payload(monkeypatch):
    task_id = "hf-skills-noop-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "target_lang": "mm",
            "title": "skills noop",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": False, "fresh": False, "url": None},
            "historical_final": {"exists": False, "url": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": False,
            "voice_exists": False,
        },
    )
    _patch_workbench_dependencies(monkeypatch)
    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", lambda _input: None)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert "advisory" not in data
    assert data.get("artifact_facts") == {
        "final_exists": False,
        "final_url": None,
        "final_updated_at": None,
        "final_asset_version": None,
        "audio_exists": False,
        "audio_url": None,
        "subtitle_exists": False,
        "subtitle_url": None,
        "pack_exists": False,
        "pack_url": None,
    }


def test_hot_follow_advisory_result_attaches_to_workbench_payload(monkeypatch):
    task_id = "hf-skills-advisory-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "target_lang": "mm",
            "title": "skills advisory",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": False, "fresh": False, "url": None},
            "historical_final": {"exists": False, "url": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": False,
            "voice_exists": False,
        },
    )
    _patch_workbench_dependencies(monkeypatch)

    captured = {}

    def _fake_advisory(advisory_input):
        captured.update(advisory_input)
        return {
            "id": "hf_advisory_v0",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "noop",
            "operator_hint": "safe",
            "explanation": "read only",
            "evidence": {"source": "test"},
        }

    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", _fake_advisory)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert captured["task"]["task_id"] == task_id
    assert captured["line"]["line_id"] == "hot_follow_line"
    assert "ready_gate" in captured
    assert "artifact_facts" in captured
    assert "current_attempt" in captured
    assert "operator_summary" in captured
    assert data.get("advisory") == {
        "id": "hf_advisory_v0",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "noop",
        "operator_hint": "safe",
        "explanation": "read only",
        "evidence": {"source": "test"},
    }

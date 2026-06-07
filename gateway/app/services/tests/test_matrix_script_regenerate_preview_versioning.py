"""Matrix Script P1 PR-2 — Regenerate Preview Versioning.

Operator loop: with a current main video (V1) and a material-replacement intent,
the operator regenerates → a V2 *candidate* preview is created WITHOUT touching
V1; the operator then sets V2 as main, discards it, or keeps tuning. Delivery
candidate follows the confirmed current main version. official_publish_ready
stays false throughout. No upload / R2 / Akool / multi-variant beyond V1/V2.

Boundary: Matrix-Script-scoped only — no Hot Follow / Digital Anchor /
artifact_storage / schema-contract / Akool surface touched.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv

INTENT_KEY = owv.MATERIAL_INTENT_KEY
V2_URL = "/api/matrix-script/ms-regen-1/preview-version/V2/final.mp4"


class _Repo:
    def __init__(self) -> None:
        self._rows: Dict[str, Dict[str, Any]] = {}

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._rows[str(payload["task_id"])] = dict(payload)
        return dict(payload)

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        row = self._rows.get(str(task_id))
        return dict(row) if row is not None else None

    def update(self, task_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        self._rows[str(task_id)].update(patch)
        return dict(self._rows[str(task_id)])


def _client(monkeypatch, repo: _Repo) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "off")
    app.dependency_overrides[get_task_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=True)


def _v1_payload() -> Dict[str, Any]:
    return {
        "has_result": True,
        "operator_usable": True,
        "delivery_candidate": True,
        "official_publish_ready": False,
        "preview_url": "/api/matrix-script/ms-regen-1/tomato-real-result/preview/final.mp4",
    }


def _task_with_v1(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config: Dict[str, Any] = {"matrix_script_staged_candidate": _v1_payload()}
    if extra:
        config.update(extra)
    return {"task_id": "ms-regen-1", "kind": "matrix_script", "config": config}


def _v2_candidate_payload() -> Dict[str, Any]:
    return {
        "has_result": True,
        "operator_usable": True,
        "delivery_candidate": True,
        "official_publish_ready": False,
        "preview_url": V2_URL,
    }


def _stub_regen(monkeypatch) -> None:
    monkeypatch.setattr(
        auto, "build_matrix_script_regeneration_payload",
        lambda task, *, material_assets=None: _v2_candidate_payload(),
    )


# --------------------------------------------------------------------------- #
# 1. Dirty intent + current V1 → A区 renders 再次生成预览.
# --------------------------------------------------------------------------- #


def _render_ms_primary_branch(overlay: Dict[str, Any]) -> str:
    from pathlib import Path
    from jinja2 import ChainableUndefined, Environment

    tpl = Path("gateway/app/templates/task_workbench.html").read_text(encoding="utf-8")
    start = tpl.index("{% if ms_main_video_result.is_matrix_script %}")
    end = tpl.index("{# Phase 2C", start)
    branch = tpl[start:end]
    return Environment(undefined=ChainableUndefined, autoescape=True).from_string(branch).render(
        ms_main_video_result={"is_matrix_script": True, "state_kind": "deliverable",
                              "state_label_zh": "运营可用", "preview": {"available": False}, "primary_actions": []},
        ms_overlay=overlay, ms_overlay_mr=overlay["main_result"],
        ms_overlay_has=overlay["main_result"]["operator_usable"],
        ms_preview_compare={"is_matrix_script": True}, task={"task_id": "ms-regen-1"},
    )


def test_dirty_intent_only_guides_to_upload_not_regenerate() -> None:
    # Observability model: a bare intent (no material yet) is intent_only and must
    # NOT offer the regenerate trigger — it guides the operator to upload first.
    task = _task_with_v1({INTENT_KEY: {"shot04": {"intent": "supplement", "updated_at": "x"}}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    assert overlay["process_state"] == "intent_only"
    html = _render_ms_primary_branch(overlay)
    assert 'data-role="ms-regen-versioning"' in html
    assert 'data-role="ms-regen-intent-only"' in html
    assert 'data-role="ms-regen-trigger"' not in html
    assert 'data-role="ms-main-video-result-video"' in html


def test_material_ready_renders_regenerate_action() -> None:
    # Once material is uploaded the shot is material_ready → regenerate is offered.
    task = _task_with_v1({INTENT_KEY: {"shot04": {
        "intent": "supplement", "updated_at": "x",
        "material_ref": "msmaterial://matrix_script/ms-regen-1/shot04/u1",
        "material_name": "fresh.png", "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace", "bytes_resolvable": True,
    }}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    assert overlay["process_state"] == "material_ready"
    html = _render_ms_primary_branch(overlay)
    assert 'data-role="ms-regen-versioning"' in html
    assert 'data-role="ms-regen-trigger"' in html
    assert "再次生成预览" in html
    # V1 current main still rendered above.
    assert 'data-role="ms-main-video-result-video"' in html


# --------------------------------------------------------------------------- #
# 2 + 3. Regenerate creates V2 candidate, preserves V1, records based_on_intents.
# --------------------------------------------------------------------------- #


def test_regenerate_creates_v2_candidate_preserving_v1(monkeypatch) -> None:
    _stub_regen(monkeypatch)
    repo = _Repo()
    repo.create(_task_with_v1({INTENT_KEY: {
        "shot04": {"intent": "supplement", "updated_at": "x"},
        "shot05": {"intent": "replace", "updated_at": "x"},
    }}))

    auto.enqueue_matrix_script_preview_regeneration(repo.get("ms-regen-1"), repo)
    status = auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-1"), repo)
    assert status["status"] == auto.STATUS_SUCCEEDED

    cfg = repo.get("ms-regen-1")["config"]
    # V1 untouched.
    assert cfg["matrix_script_staged_candidate"]["preview_url"].endswith("/tomato-real-result/preview/final.mp4")
    # V2 candidate present.
    v2 = cfg[auto.PREVIEW_VERSIONS_KEY]["V2"]
    assert v2["role"] == auto.ROLE_CANDIDATE
    assert v2["source"] == auto.SOURCE_REGENERATION
    assert v2["preview_url"] == V2_URL
    # based_on_intents records the dirty shots.
    assert v2["based_on_intents"] == ["shot04", "shot05"]


# --------------------------------------------------------------------------- #
# 4. Workbench shows V1 current main and V2 new preview distinctly.
# --------------------------------------------------------------------------- #


def test_view_projects_v1_and_v2_distinctly() -> None:
    task = _task_with_v1({auto.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": "candidate_preview", "preview_url": V2_URL,
        "created_at": "x", "source": "material_regeneration", "based_on_intents": ["shot04"],
        "payload": _v2_candidate_payload()}}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    assert view["has_candidate_preview"] is True
    assert view["current_main_version"] == "V1"
    assert view["new_preview"]["version"] == "V2"
    assert view["new_preview"]["preview_url"] == V2_URL
    assert view["new_preview"]["based_on_intents"] == ["shot04"]
    versions = {v["version"]: v for v in view["preview_versions"]}
    assert versions["V1"]["role"] == "current_main"
    assert versions["V2"]["role"] == "candidate_preview"
    # The candidate render block + V1 main video both appear.
    html = _render_ms_primary_branch(view)
    assert 'data-role="ms-regen-candidate"' in html
    assert 'data-role="ms-regen-candidate-video"' in html
    assert "设为主版本" in html and "丢弃新预览" in html and "继续调整" in html


# --------------------------------------------------------------------------- #
# 5 + 6. Confirm V2 as main → current_main_version + delivery follow V2.
# --------------------------------------------------------------------------- #


def test_confirm_v2_as_main_updates_current_main_and_delivery(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task_with_v1({
        auto.PREVIEW_VERSIONS_KEY: {"V2": {
            "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
            "source": "material_regeneration", "based_on_intents": ["shot04"],
            "payload": _v2_candidate_payload()}},
        INTENT_KEY: {"shot04": {"intent": "supplement", "updated_at": "x"}},
    }))
    client = _client(monkeypatch, repo)
    try:
        resp = client.post("/api/matrix-script/ms-regen-1/preview-version/confirm")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_main_version"] == "V2"
    assert body["delivery_candidate"] is True
    assert body["official_publish_ready"] is False

    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-1"))
    # Delivery candidate now follows V2's preview_url; candidate consumed; intents cleared.
    assert view["delivery"]["preview_url"] == V2_URL
    assert view["main_result"]["preview_url"] == V2_URL
    assert view["has_candidate_preview"] is False
    assert view["material_changed"] is False
    assert repo.get("ms-regen-1")["config"][INTENT_KEY] == {}


# --------------------------------------------------------------------------- #
# 7. Discard V2 preserves V1 as main and removes candidate.
# --------------------------------------------------------------------------- #


def test_discard_v2_preserves_v1(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task_with_v1({auto.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
        "source": "material_regeneration", "based_on_intents": ["shot04"],
        "payload": _v2_candidate_payload()}}}))
    client = _client(monkeypatch, repo)
    try:
        resp = client.post("/api/matrix-script/ms-regen-1/preview-version/discard")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["has_candidate_preview"] is False

    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-1"))
    # V1 preserved as current main; candidate gone.
    assert view["main_result"]["preview_url"].endswith("/tomato-real-result/preview/final.mp4")
    assert view["current_main_version"] == "V1"
    assert view["has_candidate_preview"] is False


# --------------------------------------------------------------------------- #
# 8 + 9. official_publish_ready false; no leakage.
# --------------------------------------------------------------------------- #


def test_official_publish_ready_false_throughout(monkeypatch) -> None:
    _stub_regen(monkeypatch)
    repo = _Repo()
    repo.create(_task_with_v1({INTENT_KEY: {"shot04": {"intent": "supplement", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo)
    try:
        assert client.post("/api/matrix-script/ms-regen-1/regenerate-preview").json()["official_publish_ready"] is False
        auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-1"), repo)
        st = client.get("/api/matrix-script/ms-regen-1/regeneration-status").json()
        assert st["official_publish_ready"] is False
        assert st["has_candidate_preview"] is True
    finally:
        app.dependency_overrides.clear()
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-1"))
    assert view["main_result"]["official_publish_ready"] is False
    assert view["delivery"]["official_publish_ready"] is False


def test_no_leakage_in_version_projection() -> None:
    task = _task_with_v1({auto.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
        "source": "material_regeneration", "based_on_intents": ["shot04"],
        "payload": _v2_candidate_payload()}}})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    blob = str(owv._scrub_operator_notes(view)).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob
    # The full candidate payload internals are not surfaced — only operator-safe fields.
    assert set(view["new_preview"].keys()) == {
        "version", "role", "label_zh", "preview_url", "based_on_intents", "source",
        # P1-2 PR-B adds the attached-material usage projection (operator-safe).
        "based_on_assets", "material_bytes_consumed", "material_usage_note_zh",
        # P1-3 PR-D adds the consumed-bytes projection (operator-safe).
        "consumed_materials",
    }


# --------------------------------------------------------------------------- #
# 10. Regeneration failure does not overwrite V1; shows retry/failure state.
# --------------------------------------------------------------------------- #


def test_regeneration_failure_preserves_v1_and_shows_retry(monkeypatch) -> None:
    def _boom(task, *, material_assets=None):
        raise auto.AutoPreviewValidationError("final_video_too_small")
    monkeypatch.setattr(auto, "build_matrix_script_regeneration_payload", _boom)
    repo = _Repo()
    repo.create(_task_with_v1({INTENT_KEY: {"shot04": {"intent": "supplement", "updated_at": "x"}}}))

    status = auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-1"), repo)
    assert status["status"] == auto.STATUS_FAILED
    assert status["stage"] == "validation"

    cfg = repo.get("ms-regen-1")["config"]
    # V1 untouched; no V2 candidate written.
    assert cfg["matrix_script_staged_candidate"]["preview_url"].endswith("/tomato-real-result/preview/final.mp4")
    assert cfg.get(auto.PREVIEW_VERSIONS_KEY, {}) == {}

    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-1"))
    assert view["regeneration"]["status"] == auto.STATUS_FAILED
    assert view["regeneration"]["poll"] is False
    assert view["regeneration"]["blocked_reason"]
    assert view["main_result"]["operator_usable"] is True  # V1 still the current main
    html = _render_ms_primary_branch(view)
    assert 'data-role="ms-regen-failed"' in html
    assert "再次生成预览" in html  # retry available

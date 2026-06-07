"""Matrix Script P1 PR-1 — Shot Material Replacement Intent.

Intent-only loop: an operator marks a shot to replace / supplement / keep its
material. Marking an intent persists to task config, makes the material dirty
(operator must regenerate), and is reflected in the Workbench projection — but
it must NOT overwrite the current main video, change the delivery candidate, or
flip official_publish_ready. No upload, no storage, no regeneration, no
versioning (those are PR-2 / later).

Boundary: Matrix-Script-scoped only — no Hot Follow / Digital Anchor /
artifact_storage / schema-contract / Akool surface touched.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

INTENT_KEY = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id
_SHOT_05 = _SHOTS[4].shot_id


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


def _ms_task(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"task_id": "ms-mat-1", "kind": "matrix_script", "config": config or {}}


def _success_staged() -> Dict[str, Any]:
    # A confirmed, operator-usable current main video (V1).
    return {
        "matrix_script_staged_candidate": {
            "has_result": True,
            "operator_usable": True,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": "/api/matrix-script/ms-mat-1/tomato-real-result/preview/final.mp4",
        }
    }


def _post_intent(client: TestClient, shot_id: str, intent: str, note: str | None = None):
    body: Dict[str, Any] = {"shot_id": shot_id, "intent": intent}
    if note is not None:
        body["operator_note"] = note
    return client.post("/api/matrix-script/ms-mat-1/material-replacement-intent", json=body)


# --------------------------------------------------------------------------- #
# 1 + 2. Intent persists to task config.
# --------------------------------------------------------------------------- #


def test_mark_shot04_supplement_intent_persists(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task())
    client = _client(monkeypatch, repo)
    try:
        resp = _post_intent(client, _SHOT_04, "supplement", note="补充真实品尝素材")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["material_changed"] is True
    assert body["dirty_shot_count"] == 1
    assert body["official_publish_ready"] is False
    entry = (repo.get("ms-mat-1") or {})["config"][INTENT_KEY][_SHOT_04]
    assert entry["intent"] == "supplement"
    assert entry["operator_note"] == "补充真实品尝素材"
    assert entry["updated_at"]


def test_mark_shot05_replace_intent_persists(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task())
    client = _client(monkeypatch, repo)
    try:
        resp = _post_intent(client, _SHOT_05, "replace")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    entry = (repo.get("ms-mat-1") or {})["config"][INTENT_KEY][_SHOT_05]
    assert entry["intent"] == "replace"


def test_keep_intent_clears_prior_dirty(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task({INTENT_KEY: {_SHOT_04: {"intent": "supplement", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo)
    try:
        resp = _post_intent(client, _SHOT_04, "keep")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["material_changed"] is False
    assert _SHOT_04 not in (repo.get("ms-mat-1") or {})["config"].get(INTENT_KEY, {})


def test_intent_endpoint_validates(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task())
    client = _client(monkeypatch, repo)
    try:
        assert client.post("/api/matrix-script/ms-mat-1/material-replacement-intent",
                           json={"shot_id": "nope", "intent": "replace"}).status_code == 400
        assert client.post("/api/matrix-script/ms-mat-1/material-replacement-intent",
                           json={"shot_id": _SHOT_04, "intent": "bogus"}).status_code == 400
        repo.create({"task_id": "hf-1", "kind": "hot_follow", "config": {}})
        assert client.post("/api/matrix-script/hf-1/material-replacement-intent",
                           json={"shot_id": _SHOT_04, "intent": "replace"}).status_code == 400
        assert client.post("/api/matrix-script/missing/material-replacement-intent",
                           json={"shot_id": _SHOT_04, "intent": "replace"}).status_code == 404
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# 3 + 4 + 5. Projection: B区 dirty shot status, A区 dirty state, main video kept.
# --------------------------------------------------------------------------- #


def test_view_projects_dirty_shot_status() -> None:
    task = _ms_task({**_success_staged(), INTENT_KEY: {_SHOT_04: {"intent": "supplement", "updated_at": "x"}}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    assert view["material_changed"] is True
    assert view["dirty_shot_count"] == 1
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["intent"] == "supplement"
    assert by_id[_SHOT_04]["intent_dirty"] is True
    assert by_id[_SHOT_04]["intent_label_zh"] == "已标记补充素材"
    # Untouched shots remain non-dirty / keep.
    assert by_id[_SHOT_05]["intent"] == "keep"
    assert by_id[_SHOT_05]["intent_dirty"] is False


def test_view_no_intents_is_not_dirty() -> None:
    view = owv.build_matrix_script_operator_workbench_view(_ms_task(_success_staged()))
    assert view["material_changed"] is False
    assert view["dirty_shot_count"] == 0
    assert all(not s["intent_dirty"] for s in view["shots"])


def _render_ms_primary_branch(overlay: Dict[str, Any]) -> str:
    """Render the isolated matrix_script primary branch with the REAL builder overlay."""
    from pathlib import Path

    from jinja2 import ChainableUndefined, Environment

    tpl = Path("gateway/app/templates/task_workbench.html").read_text(encoding="utf-8")
    start = tpl.index("{% if ms_main_video_result.is_matrix_script %}")
    end = tpl.index("{# Phase 2C", start)
    branch = tpl[start:end]
    return Environment(undefined=ChainableUndefined, autoescape=True).from_string(branch).render(
        ms_main_video_result={"is_matrix_script": True, "state_kind": "deliverable",
                              "state_label_zh": "运营可用", "preview": {"available": False}, "primary_actions": []},
        ms_overlay=overlay,
        ms_overlay_mr=overlay["main_result"],
        ms_overlay_has=overlay["main_result"]["operator_usable"],
        ms_preview_compare={"is_matrix_script": True},
        task={"task_id": "ms-mat-1"},
    )


def test_workbench_renders_dirty_state_a_and_b() -> None:
    task = _ms_task({**_success_staged(), INTENT_KEY: {_SHOT_04: {"intent": "supplement", "updated_at": "x"}}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(overlay)
    # Observability model: a bare intent (no material) is intent_only — the A区
    # guidance is "已记录素材调整意图", NOT the regenerate prompt.
    assert overlay["process_state"] == "intent_only"
    assert "已记录素材调整意图" in html
    assert "素材已更新，需要再次生成预览" not in html
    assert 'data-role="ms-primary-material-dirty-summary"' in html
    assert "已标记补充素材" in html
    # Current main video (V1) still rendered via the staged preview, not overwritten.
    assert 'data-role="ms-main-video-result-video"' in html
    assert "/tomato-real-result/preview/final.mp4" in html
    # The three intent actions are present per shot.
    assert html.count('data-role="ms-primary-shot-intent-supplement"') == len(_SHOTS)


# --------------------------------------------------------------------------- #
# 6 + 8. Delivery protection: dirty intent never flips publish readiness.
# --------------------------------------------------------------------------- #


def test_dirty_material_does_not_become_publish_ready() -> None:
    task = _ms_task({**_success_staged(), INTENT_KEY: {_SHOT_04: {"intent": "replace", "updated_at": "x"}}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    assert view["main_result"]["official_publish_ready"] is False
    assert view["delivery"]["official_publish_ready"] is False
    # Delivery candidate still tied to the confirmed current main video, unchanged
    # by the dirty intent.
    assert view["delivery"]["delivery_candidate"] is True
    assert view["main_result"]["operator_usable"] is True


# --------------------------------------------------------------------------- #
# 7. No provider/artifact/raw-manifest leakage — even with operator note text.
# --------------------------------------------------------------------------- #


def test_no_leakage_with_operator_note() -> None:
    # Operator note containing a would-be forbidden token must not crash the
    # render guard (operator prose is excluded from the engineering scan).
    task = _ms_task({INTENT_KEY: {_SHOT_04: {"intent": "supplement", "operator_note": "akool 风格更好", "updated_at": "x"}}})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["intent_note"] == "akool 风格更好"
    # The projection's own fields carry no provider/publish identifiers.
    scrubbed = owv._scrub_operator_notes(view)
    blob = str(scrubbed).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob

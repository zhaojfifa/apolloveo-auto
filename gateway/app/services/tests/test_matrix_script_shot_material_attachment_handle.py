"""Matrix Script P1-2 PR-A — Shot Material Attachment Handle.

A shot replace/supplement intent can carry a concrete material attachment
reference (an existing asset handle / operator language). Binding is a HANDLE
only: regeneration does NOT consume it yet (PR-B). Binding makes/keeps the shot
dirty ("已绑定，等待再次生成预览") but must NOT overwrite the current main video
(V1), create or overwrite a V2 candidate, change the delivery candidate, or flip
official_publish_ready. Missing attachment on a dirty shot shows 待补素材.

Boundary: Matrix-Script-scoped only — no upload/R2 binary, no Akool live, no
Hot Follow / Digital Anchor / artifact_storage / schema-contract surface.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

INTENT_KEY = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id
_SHOT_05 = _SHOTS[4].shot_id
V1_URL = "/api/matrix-script/ms-att-1/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-att-1/preview-version/V2/final.mp4"
ATTACH_ROUTE = "/api/matrix-script/ms-att-1/shot-material-attachment"


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


def _v1_staged() -> Dict[str, Any]:
    return {
        "matrix_script_staged_candidate": {
            "has_result": True,
            "operator_usable": True,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": V1_URL,
        }
    }


def _ms_task(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"task_id": "ms-att-1", "kind": "matrix_script", "config": config or {}}


def _attach(client: TestClient, shot_id: str, **fields):
    body: Dict[str, Any] = {"shot_id": shot_id}
    body.update(fields)
    return client.post(ATTACH_ROUTE, json=body)


# --------------------------------------------------------------------------- #
# 1 + 2. Attach material_ref to Shot 04 supplement / Shot 05 replace.
# --------------------------------------------------------------------------- #


def test_attach_material_to_shot04_supplement(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_04: {"intent": "supplement", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo)
    try:
        resp = _attach(
            client, _SHOT_04,
            material_ref="asset://matrix_script/ms-att-1/shot04/a1",
            material_name="tomato_tasting_closeup.mp4",
            material_kind="video",
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["material_attached"] is True
    assert body["intent"] == "supplement"
    assert body["material_changed"] is True
    assert body["official_publish_ready"] is False
    entry = (repo.get("ms-att-1") or {})["config"][INTENT_KEY][_SHOT_04]
    assert entry["material_ref"] == "asset://matrix_script/ms-att-1/shot04/a1"
    assert entry["material_name"] == "tomato_tasting_closeup.mp4"
    assert entry["material_kind"] == "video"
    assert entry["material_source"] == "operator_attachment"
    assert entry["updated_at"]


def test_attach_material_to_shot05_replace(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo)
    try:
        resp = _attach(
            client, _SHOT_05,
            material_ref="asset://matrix_script/ms-att-1/shot05/b2",
            material_name="hand_reaching_shot.png",
            material_kind="image",
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["intent"] == "replace"
    entry = (repo.get("ms-att-1") or {})["config"][INTENT_KEY][_SHOT_05]
    assert entry["material_kind"] == "image"
    assert entry["intent"] == "replace"


def test_attach_without_prior_intent_defaults_supplement(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task(_v1_staged()))
    client = _client(monkeypatch, repo)
    try:
        resp = _attach(
            client, _SHOT_04,
            material_ref="asset://matrix_script/ms-att-1/shot04/c3",
            material_name="fresh.mp4", material_kind="video",
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["intent"] == "supplement"
    assert resp.json()["material_changed"] is True


def test_attach_validates(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task(_v1_staged()))
    client = _client(monkeypatch, repo)
    try:
        # unknown shot
        assert _attach(client, "nope", material_ref="r", material_name="n", material_kind="video").status_code == 400
        # missing ref
        assert _attach(client, _SHOT_04, material_name="n", material_kind="video").status_code == 400
        # missing name
        assert _attach(client, _SHOT_04, material_ref="r", material_kind="video").status_code == 400
        # bad kind
        assert _attach(client, _SHOT_04, material_ref="r", material_name="n", material_kind="gif").status_code == 400
        # non matrix-script task
        repo.create({"task_id": "hf-1", "kind": "hot_follow", "config": {}})
        assert client.post(
            "/api/matrix-script/hf-1/shot-material-attachment",
            json={"shot_id": _SHOT_04, "material_ref": "r", "material_name": "n", "material_kind": "video"},
        ).status_code == 400
        # missing task
        assert client.post(
            "/api/matrix-script/missing/shot-material-attachment",
            json={"shot_id": _SHOT_04, "material_ref": "r", "material_name": "n", "material_kind": "video"},
        ).status_code == 404
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# 3 + 4. Projection + render: B区 shows attachment / 待补素材.
# --------------------------------------------------------------------------- #


def test_view_projects_attachment_fields() -> None:
    task = _ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_04: {
        "intent": "supplement", "updated_at": "x",
        "material_ref": "asset://matrix_script/ms-att-1/shot04/a1",
        "material_name": "tomato_tasting_closeup.mp4",
        "material_kind": "video", "material_source": "operator_attachment",
    }}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    by_id = {s["shot_id"]: s for s in view["shots"]}
    s4 = by_id[_SHOT_04]
    assert s4["material_attached"] is True
    assert s4["material_name"] == "tomato_tasting_closeup.mp4"
    assert s4["material_kind"] == "video"
    assert s4["material_kind_label_zh"] == "视频"
    assert s4["material_source_label_zh"] == "运营补充素材"
    assert s4["material_status_zh"] == "已绑定，等待再次生成预览"
    # A shot with no attachment is not attached.
    assert by_id[_SHOT_05]["material_attached"] is False


def test_view_dirty_unattached_shows_pending() -> None:
    task = _ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_05]["material_attached"] is False
    assert by_id[_SHOT_05]["material_status_zh"] == "待补素材"


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
        ms_overlay=overlay,
        ms_overlay_mr=overlay["main_result"],
        ms_overlay_has=overlay["main_result"]["operator_usable"],
        ms_preview_compare={"is_matrix_script": True},
        task={"task_id": "ms-att-1"},
    )


def test_workbench_b_zone_displays_attachment() -> None:
    task = _ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_04: {
        "intent": "supplement", "updated_at": "x",
        "material_ref": "asset://matrix_script/ms-att-1/shot04/a1",
        "material_name": "tomato_tasting_closeup.mp4",
        "material_kind": "video", "material_source": "operator_attachment",
    }}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(overlay)
    assert 'data-role="ms-primary-shot-material-attachment"' in html
    assert "tomato_tasting_closeup.mp4" in html
    assert "素材类型：视频" in html
    assert "来源：运营补充素材" in html
    assert "已绑定，等待再次生成预览" in html
    # Placeholder thumbnail when no thumbnail_url is bound.
    assert 'data-role="ms-primary-shot-material-thumb-placeholder"' in html
    # One per-shot attach form is present for every shot (exact element match;
    # the bare data-role avoids the JS selector + -form/-submit substrings).
    assert html.count('data-role="ms-primary-shot-material-attach"') == len(_SHOTS)
    assert 'data-role="ms-primary-shot-material-attach-submit"' in html
    # V1 current main still rendered, not overwritten by the attachment.
    assert 'data-role="ms-main-video-result-video"' in html
    assert "/tomato-real-result/preview/final.mp4" in html


def test_workbench_b_zone_shows_pending_for_unattached_dirty() -> None:
    task = _ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(overlay)
    assert "待补素材" in html


# --------------------------------------------------------------------------- #
# 5 + 6. A区 dirty banner remains; V1 main preserved by binding (route-driven).
# --------------------------------------------------------------------------- #


def test_attach_keeps_dirty_and_preserves_v1(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task(_v1_staged()))
    client = _client(monkeypatch, repo)
    try:
        _attach(
            client, _SHOT_04,
            material_ref="asset://matrix_script/ms-att-1/shot04/a1",
            material_name="fresh.mp4", material_kind="video",
        )
    finally:
        app.dependency_overrides.clear()
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-att-1"))
    # A区 dirty state remains.
    assert view["material_changed"] is True
    assert view["dirty_shot_count"] >= 1
    # V1 main video unchanged.
    assert view["main_result"]["preview_url"] == V1_URL
    assert view["main_result"]["operator_usable"] is True
    assert view["current_main_version"] == "V1"


# --------------------------------------------------------------------------- #
# 7. Existing V2 candidate is not overwritten by an attachment.
# --------------------------------------------------------------------------- #


def test_attach_does_not_overwrite_existing_v2(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task({
        **_v1_staged(),
        auto.PREVIEW_VERSIONS_KEY: {"V2": {
            "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
            "source": "material_regeneration", "based_on_intents": ["shot04"],
            "payload": {"has_result": True, "operator_usable": True,
                        "delivery_candidate": True, "official_publish_ready": False,
                        "preview_url": V2_URL}},
        },
    }))
    client = _client(monkeypatch, repo)
    try:
        resp = _attach(
            client, _SHOT_05,
            material_ref="asset://matrix_script/ms-att-1/shot05/z9",
            material_name="late.mp4", material_kind="video",
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    cfg = repo.get("ms-att-1")["config"]
    # V2 candidate slot untouched.
    v2 = cfg[auto.PREVIEW_VERSIONS_KEY]["V2"]
    assert v2["preview_url"] == V2_URL
    assert v2["based_on_intents"] == ["shot04"]
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-att-1"))
    assert view["has_candidate_preview"] is True
    assert view["new_preview"]["preview_url"] == V2_URL


# --------------------------------------------------------------------------- #
# 8 + 9. Delivery candidate tied to confirmed main; official_publish_ready=false.
# --------------------------------------------------------------------------- #


def test_attach_delivery_protected_and_not_publish_ready(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_ms_task(_v1_staged()))
    client = _client(monkeypatch, repo)
    try:
        _attach(
            client, _SHOT_04,
            material_ref="asset://matrix_script/ms-att-1/shot04/a1",
            material_name="fresh.mp4", material_kind="video",
        )
    finally:
        app.dependency_overrides.clear()
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-att-1"))
    # Delivery candidate still tied to the confirmed current main (V1).
    assert view["delivery"]["delivery_candidate"] is True
    assert view["delivery"]["preview_url"] == V1_URL
    assert view["delivery"]["official_publish_ready"] is False
    assert view["main_result"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# 10. No provider/artifact/raw-manifest/publish-URL leakage in the projection.
# --------------------------------------------------------------------------- #


def test_no_leakage_with_attachment_and_note() -> None:
    task = _ms_task({**_v1_staged(), INTENT_KEY: {_SHOT_04: {
        "intent": "supplement", "updated_at": "x",
        "material_ref": "asset://matrix_script/ms-att-1/shot04/a1",
        "material_name": "tomato_tasting_closeup.mp4",
        "material_kind": "video", "material_source": "operator_attachment",
        "thumbnail_url": "/api/matrix-script/ms-att-1/shot04/thumb.jpg",
        "operator_note": "akool 风格更好",
    }}})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["thumbnail_url"] == "/api/matrix-script/ms-att-1/shot04/thumb.jpg"
    scrubbed = owv._scrub_operator_notes(view)
    blob = str(scrubbed).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob

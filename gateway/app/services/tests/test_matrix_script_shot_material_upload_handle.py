"""Matrix Script P1-3 PR-C — Shot Material Upload / Storage Handle.

Upgrades a shot's attached material from a bare operator reference (PR-A) to a
STORED handle whose bytes are resolvable: an operator uploads a material file, it
is persisted under a Matrix-Script-scoped local workspace path, and the shot
intent entry records bytes_resolvable=true / storage_scope=local_workspace /
material_source=operator_upload + a resolvable handle + preview.

This PR makes bytes RESOLVABLE; it does NOT make V2 regeneration CONSUME them
(material_bytes_consumed stays false — that is PR-D). Upload keeps the shot dirty
and never overwrites V1, an existing V2 candidate, or the delivery candidate;
official_publish_ready stays false.

Boundary: Matrix-Script-scoped only — no artifact_storage.py modification, no
Akool live, no provider switching, no schema/contract surface.
"""
from __future__ import annotations

import types
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import shot_material_storage as storage

INTENT_KEY = owv.MATERIAL_INTENT_KEY
TID = "ms-upload-1"
V1_URL = "/api/matrix-script/%s/tomato-real-result/preview/final.mp4" % TID
V2_URL = "/api/matrix-script/%s/preview-version/V2/final.mp4" % TID
UPLOAD = "/api/matrix-script/%s/shot-material-upload" % TID


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


def _client(monkeypatch, repo: _Repo, tmp_path) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "off")
    # Isolate storage to a tmp workspace so uploads never touch the real workspace.
    monkeypatch.setattr(storage, "get_settings", lambda: types.SimpleNamespace(workspace_root=str(tmp_path)))
    app.dependency_overrides[get_task_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=True)


def _v1() -> Dict[str, Any]:
    return {"matrix_script_staged_candidate": {
        "has_result": True, "operator_usable": True, "delivery_candidate": True,
        "official_publish_ready": False, "preview_url": V1_URL}}


def _task(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = dict(_v1())
    if extra:
        cfg.update(extra)
    return {"task_id": TID, "kind": "matrix_script", "config": cfg}


def _upload(client, shot_id, filename, data, kind=None):
    files = {"file": (filename, data, "application/octet-stream")}
    form = {"shot_id": shot_id}
    if kind is not None:
        form["material_kind"] = kind
    return client.post(UPLOAD, files=files, data=form)


# --------------------------------------------------------------------------- #
# 1 + 2 + 3. Upload image (Shot 05) / video (Shot 04); records bytes_resolvable.
# --------------------------------------------------------------------------- #


def test_upload_image_for_shot05(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": {"intent": "replace", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo, tmp_path)
    try:
        resp = _upload(client, "shot05", "reach.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, kind="image")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["material_attached"] is True
    assert body["material_kind"] == "image"
    assert body["material_source"] == "operator_upload"
    assert body["storage_scope"] == "local_workspace"
    assert body["bytes_resolvable"] is True
    assert body["intent"] == "replace"
    assert body["official_publish_ready"] is False
    entry = repo.get(TID)["config"][INTENT_KEY]["shot05"]
    assert entry["bytes_resolvable"] is True
    assert entry["material_ref"].startswith("msmaterial://")
    assert entry["material_source"] == "operator_upload"
    assert entry["storage_scope"] == "local_workspace"
    assert entry["local_path"]


def test_upload_video_for_shot04(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot04": {"intent": "supplement", "updated_at": "x"}}}))
    client = _client(monkeypatch, repo, tmp_path)
    try:
        resp = _upload(client, "shot04", "tasting.mp4", b"\x00\x00\x00\x18ftyp" + b"0" * 64, kind="video")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["material_kind"] == "video"
    assert resp.json()["bytes_resolvable"] is True
    entry = repo.get(TID)["config"][INTENT_KEY]["shot04"]
    assert entry["material_kind"] == "video"
    assert entry["intent"] == "supplement"


def test_upload_without_prior_intent_defaults_supplement(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task())
    client = _client(monkeypatch, repo, tmp_path)
    try:
        resp = _upload(client, "shot04", "fresh.png", b"img" + b"0" * 40)
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["intent"] == "supplement"
    assert resp.json()["material_changed"] is True


# --------------------------------------------------------------------------- #
# 4. Workbench B区 shows uploaded material metadata.
# --------------------------------------------------------------------------- #


def _uploaded_entry() -> Dict[str, Any]:
    return {
        "intent": "replace", "updated_at": "x",
        "material_ref": "msmaterial://%s/shot05/reach.png" % TID,
        "material_name": "reach.png", "material_kind": "image",
        "material_source": "operator_upload", "storage_scope": "local_workspace",
        "local_path": "/tmp/whatever/reach.png",
        "preview_url": "/api/matrix-script/%s/shot-material/shot05/file" % TID,
        "thumbnail_url": "/api/matrix-script/%s/shot-material/shot05/file" % TID,
        "bytes_resolvable": True,
    }


def test_view_projects_uploaded_material() -> None:
    task = _task({INTENT_KEY: {"shot05": _uploaded_entry()}})
    view = owv.build_matrix_script_operator_workbench_view(task)
    s5 = {s["shot_id"]: s for s in view["shots"]}["shot05"]
    assert s5["material_attached"] is True
    assert s5["material_source_label_zh"] == "运营上传素材"
    assert s5["material_status_zh"] == "已上传，等待再次生成预览"
    assert s5["bytes_resolvable"] is True
    assert s5["storage_scope"] == "local_workspace"
    assert s5["preview_url"].endswith("/shot-material/shot05/file")
    # Internal absolute local_path is NOT surfaced in the operator projection.
    assert "local_path" not in s5


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
        ms_preview_compare={"is_matrix_script": True}, task={"task_id": TID},
    )


def test_workbench_b_zone_shows_uploaded_material() -> None:
    task = _task({INTENT_KEY: {"shot05": _uploaded_entry()}})
    overlay = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(overlay)
    assert "reach.png" in html
    assert "来源：运营上传素材" in html
    assert "已上传，等待再次生成预览" in html
    # Upload form present per shot.
    assert html.count('data-role="ms-primary-shot-material-upload"') == len(list(owv.plan_mod.TOMATO_SHOTS))
    # Internal absolute path never rendered.
    assert "/tmp/whatever/reach.png" not in html


# --------------------------------------------------------------------------- #
# 5 + 6 + 7 + 8 + 9. State protection.
# --------------------------------------------------------------------------- #


def test_upload_keeps_dirty_preserves_v1_and_v2_and_delivery(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task({
        auto.PREVIEW_VERSIONS_KEY: {"V2": {
            "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
            "source": "material_regeneration", "based_on_intents": ["shot04"],
            "based_on_assets": [], "material_bytes_consumed": False,
            "payload": {"has_result": True, "operator_usable": True,
                        "delivery_candidate": True, "official_publish_ready": False,
                        "preview_url": V2_URL}}},
    }))
    client = _client(monkeypatch, repo, tmp_path)
    try:
        assert _upload(client, "shot05", "reach.png", b"img" + b"0" * 40, kind="image").status_code == 200
    finally:
        app.dependency_overrides.clear()
    cfg = repo.get(TID)["config"]
    # V1 untouched.
    assert cfg["matrix_script_staged_candidate"]["preview_url"] == V1_URL
    # Existing V2 candidate not overwritten.
    assert cfg[auto.PREVIEW_VERSIONS_KEY]["V2"]["preview_url"] == V2_URL
    assert cfg[auto.PREVIEW_VERSIONS_KEY]["V2"]["based_on_intents"] == ["shot04"]
    view = owv.build_matrix_script_operator_workbench_view(repo.get(TID))
    assert view["material_changed"] is True
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL
    # Delivery tied to confirmed main; not publish-ready.
    assert view["delivery"]["preview_url"] == V1_URL
    assert view["delivery"]["official_publish_ready"] is False
    assert view["has_candidate_preview"] is True


def test_material_bytes_consumed_stays_false_after_upload(monkeypatch, tmp_path) -> None:
    # PR-C boundary: upload makes bytes RESOLVABLE but regeneration must NOT
    # consume them yet — the regen resolver still returns None for the handle.
    repo = _Repo()
    repo.create(_task())
    client = _client(monkeypatch, repo, tmp_path)
    try:
        _upload(client, "shot04", "tasting.mp4", b"\x00\x00\x00\x18ftyp" + b"0" * 64, kind="video")
    finally:
        app.dependency_overrides.clear()
    entry = repo.get(TID)["config"][INTENT_KEY]["shot04"]
    # The regeneration-layer resolver does NOT resolve the stored handle to bytes
    # in this PR (that wiring is PR-D), so material_bytes_consumed stays false.
    assert auto.resolve_material_asset_bytes_path(entry["material_ref"]) is None
    assets = auto._material_attachment_assets(repo.get(TID))
    overrides = auto._material_overrides_from_assets(assets)
    assert overrides == {}


# --------------------------------------------------------------------------- #
# 10. No leakage in primary UI.
# --------------------------------------------------------------------------- #


def test_no_leakage_with_uploaded_material() -> None:
    task = _task({INTENT_KEY: {"shot05": _uploaded_entry()}})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    blob = str(owv._scrub_operator_notes(view)).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob


# --------------------------------------------------------------------------- #
# 11. Invalid file kind / oversized / missing rejected safely.
# --------------------------------------------------------------------------- #


def test_upload_rejects_unsupported_kind(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task())
    client = _client(monkeypatch, repo, tmp_path)
    try:
        r = _upload(client, "shot04", "evil.exe", b"MZ" + b"0" * 40)
        assert r.status_code == 400
        # kind mismatch: .png declared as video
        r2 = _upload(client, "shot04", "pic.png", b"img" + b"0" * 40, kind="video")
        assert r2.status_code == 400
        # unknown shot
        r3 = _upload(client, "nope", "x.png", b"img" + b"0" * 40)
        assert r3.status_code == 400
    finally:
        app.dependency_overrides.clear()
    # No intent entry written on rejection.
    assert repo.get(TID)["config"].get(INTENT_KEY, {}) == {}


def test_upload_rejects_oversized(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MATRIX_SCRIPT_MATERIAL_MAX_MB", "1")
    repo = _Repo()
    repo.create(_task())
    client = _client(monkeypatch, repo, tmp_path)
    try:
        big = b"0" * (2 * 1024 * 1024)  # 2MB > 1MB cap
        r = _upload(client, "shot04", "big.mp4", big, kind="video")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 400


def test_upload_rejects_non_matrix_script_and_missing(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task())
    repo.create({"task_id": "hf-1", "kind": "hot_follow", "config": {}})
    client = _client(monkeypatch, repo, tmp_path)
    try:
        r = client.post("/api/matrix-script/hf-1/shot-material-upload",
                        files={"file": ("x.png", b"img" + b"0" * 40, "image/png")},
                        data={"shot_id": "shot04"})
        assert r.status_code == 400
        r2 = client.post("/api/matrix-script/missing/shot-material-upload",
                         files={"file": ("x.png", b"img" + b"0" * 40, "image/png")},
                         data={"shot_id": "shot04"})
        assert r2.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_uploaded_file_is_servable(monkeypatch, tmp_path) -> None:
    repo = _Repo()
    repo.create(_task())
    client = _client(monkeypatch, repo, tmp_path)
    try:
        _upload(client, "shot05", "reach.png", b"\x89PNG" + b"0" * 80, kind="image")
        resp = client.get("/api/matrix-script/%s/shot-material/shot05/file" % TID)
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.content.startswith(b"\x89PNG")


# --------------------------------------------------------------------------- #
# 12. Engineering index reflects P1-3 PR-C active focus.
# --------------------------------------------------------------------------- #


def test_engineering_index_records_p1_3_focus() -> None:
    from pathlib import Path

    idx = Path("docs/ENGINEERING_INDEX.md").read_text(encoding="utf-8")
    assert "Matrix Script P1-3 PR-C" in idx
    assert "Shot Material Upload / Storage Handle" in idx
    assert "bytes_resolvable" in idx

"""Matrix Script P1-2 PR-B — Regenerate Uses Attached Material.

A V2 regeneration now CONSUMES the Shot-level attached material handles produced
by PR-A, instead of only recording the bare intent. The V2 candidate records
``based_on_assets`` (shot_id / material_ref / material_name / material_kind). The
attachment handles are operator references (``asset://...``) with no byte store
yet, so the renderer does not perform a real pixel replacement — the projection
is HONEST about that ("已绑定运营素材引用，当前预览以素材引用标记生成。") and never
claims "真实替换画面".

State rules preserved from PR-2: V1 stays current main until confirm; V2 is a
candidate only; confirm switches current_main_version=V2 and delivery follows it;
discard preserves V1; regeneration failure preserves V1; official_publish_ready
stays false throughout.

Boundary: Matrix-Script-scoped only — no binary upload / R2, no Akool live, no
provider switching, no multi-variant beyond V1/V2, no Hot Follow / Digital
Anchor / artifact_storage / schema-contract surface.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv

INTENT_KEY = owv.MATERIAL_INTENT_KEY
V1_URL = "/api/matrix-script/ms-regen-2/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-regen-2/preview-version/V2/final.mp4"
REF_04 = "asset://matrix_script/ms-regen-2/shot04/a1"
REF_05 = "asset://matrix_script/ms-regen-2/shot05/b2"


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
        "has_result": True, "operator_usable": True, "delivery_candidate": True,
        "official_publish_ready": False, "preview_url": V1_URL,
    }


def _v2_candidate_payload() -> Dict[str, Any]:
    return {
        "has_result": True, "operator_usable": True, "delivery_candidate": True,
        "official_publish_ready": False, "preview_url": V2_URL,
    }


def _attached_intents() -> Dict[str, Any]:
    return {
        "shot04": {"intent": "supplement", "updated_at": "x", "material_ref": REF_04,
                   "material_name": "番茄品尝特写", "material_kind": "video",
                   "material_source": "operator_attachment"},
        "shot05": {"intent": "replace", "updated_at": "x", "material_ref": REF_05,
                   "material_name": "递向镜头静帧", "material_kind": "image",
                   "material_source": "operator_attachment"},
    }


def _task(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config: Dict[str, Any] = {"matrix_script_staged_candidate": _v1_payload()}
    if extra:
        config.update(extra)
    return {"task_id": "ms-regen-2", "kind": "matrix_script", "config": config}


def _stub_regen(monkeypatch) -> None:
    monkeypatch.setattr(
        auto, "build_matrix_script_regeneration_payload",
        lambda task, *, material_assets=None: _v2_candidate_payload(),
    )


# --------------------------------------------------------------------------- #
# 1 + 2 + 3. Regeneration reads attached material; records based_on_assets.
# --------------------------------------------------------------------------- #


def test_regeneration_reads_attached_material_and_records_based_on_assets(monkeypatch) -> None:
    _stub_regen(monkeypatch)
    repo = _Repo()
    repo.create(_task({INTENT_KEY: _attached_intents()}))

    status = auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-2"), repo)
    assert status["status"] == auto.STATUS_SUCCEEDED

    v2 = repo.get("ms-regen-2")["config"][auto.PREVIEW_VERSIONS_KEY]["V2"]
    # based_on_intents still recorded.
    assert v2["based_on_intents"] == ["shot04", "shot05"]
    # based_on_assets records the attached handle for each dirty shot (sorted).
    assets = v2["based_on_assets"]
    by_shot = {a["shot_id"]: a for a in assets}
    assert by_shot["shot04"]["material_ref"] == REF_04
    assert by_shot["shot04"]["material_name"] == "番茄品尝特写"
    assert by_shot["shot04"]["material_kind"] == "video"
    assert by_shot["shot05"]["material_ref"] == REF_05
    assert by_shot["shot05"]["material_kind"] == "image"
    # Honest: asset:// handles carry no bytes, so no real pixel replacement.
    assert v2["material_bytes_consumed"] is False


def test_regeneration_ignores_dirty_shot_without_attachment(monkeypatch) -> None:
    _stub_regen(monkeypatch)
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {
        "shot04": {"intent": "supplement", "updated_at": "x", "material_ref": REF_04,
                   "material_name": "番茄品尝特写", "material_kind": "video"},
        "shot05": {"intent": "replace", "updated_at": "x"},  # dirty, no attachment
    }}))
    auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-2"), repo)
    v2 = repo.get("ms-regen-2")["config"][auto.PREVIEW_VERSIONS_KEY]["V2"]
    # Both shots are dirty intents...
    assert v2["based_on_intents"] == ["shot04", "shot05"]
    # ...but only the attached shot contributes a material asset.
    assert [a["shot_id"] for a in v2["based_on_assets"]] == ["shot04"]


def test_resolver_returns_none_for_asset_handles() -> None:
    # asset:// operator handles never resolve to local bytes in this PR.
    assert auto.resolve_material_asset_bytes_path(REF_04) is None
    assert auto.resolve_material_asset_bytes_path("") is None
    assert auto.resolve_material_asset_bytes_path(None) is None


# --------------------------------------------------------------------------- #
# 4 + 9. Workbench V2 block shows usage; honest copy (no real-replacement claim).
# --------------------------------------------------------------------------- #


def _v2_slot(consumed: bool = False) -> Dict[str, Any]:
    return {"V2": {
        "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
        "source": "material_regeneration", "based_on_intents": ["shot04", "shot05"],
        "based_on_assets": [
            {"shot_id": "shot04", "material_ref": REF_04, "material_name": "番茄品尝特写", "material_kind": "video"},
            {"shot_id": "shot05", "material_ref": REF_05, "material_name": "递向镜头静帧", "material_kind": "image"},
        ],
        "material_bytes_consumed": consumed,
        "payload": _v2_candidate_payload()}}


def test_view_projects_v2_material_usage() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=False)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    np = view["new_preview"]
    assert np["material_bytes_consumed"] is False
    assert np["material_usage_note_zh"] == "已绑定运营素材引用，当前预览以素材引用标记生成。"
    by_shot = {a["shot_id"]: a for a in np["based_on_assets"]}
    assert by_shot["shot04"]["shot_label_zh"] == "Shot 04"
    assert by_shot["shot04"]["material_name"] == "番茄品尝特写"
    assert by_shot["shot04"]["material_kind_label_zh"] == "视频"
    assert by_shot["shot05"]["material_kind_label_zh"] == "图片"


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
        ms_preview_compare={"is_matrix_script": True}, task={"task_id": "ms-regen-2"},
    )


def test_workbench_v2_block_shows_attached_material_usage_honestly() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=False)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(view)
    assert 'data-role="ms-regen-material-usage"' in html
    assert 'data-role="ms-regen-material-asset"' in html
    assert "Shot 04：番茄品尝特写（视频）" in html
    assert "Shot 05：递向镜头静帧（图片）" in html
    # Honest copy: reference-label, not a real pixel-replacement claim.
    assert "已绑定运营素材引用，当前预览以素材引用标记生成。" in html
    assert "真实替换画面" not in html


def test_workbench_v2_consumed_copy_when_bytes_used() -> None:
    # Forward-compat: when bytes ARE consumed the copy switches to the used form.
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=True)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    assert view["new_preview"]["material_usage_note_zh"] == "已使用运营补充素材"
    html = _render_ms_primary_branch(view)
    assert "已使用运营补充素材" in html


# --------------------------------------------------------------------------- #
# 5 + 6 + 7. V1 preserved before confirm; confirm follows V2; discard keeps V1.
# --------------------------------------------------------------------------- #


def test_v1_remains_current_before_confirm() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(), INTENT_KEY: _attached_intents()})
    view = owv.build_matrix_script_operator_workbench_view(task)
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL
    assert view["delivery"]["preview_url"] == V1_URL
    assert view["has_candidate_preview"] is True


def test_confirm_v2_updates_delivery(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(), INTENT_KEY: _attached_intents()}))
    client = _client(monkeypatch, repo)
    try:
        resp = client.post("/api/matrix-script/ms-regen-2/preview-version/confirm")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["current_main_version"] == "V2"
    assert resp.json()["official_publish_ready"] is False
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-2"))
    assert view["delivery"]["preview_url"] == V2_URL
    assert view["main_result"]["preview_url"] == V2_URL
    assert view["has_candidate_preview"] is False
    # Intents (and their attachments) consumed/cleared on confirm.
    assert repo.get("ms-regen-2")["config"][INTENT_KEY] == {}


def test_discard_v2_preserves_v1(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(), INTENT_KEY: _attached_intents()}))
    client = _client(monkeypatch, repo)
    try:
        resp = client.post("/api/matrix-script/ms-regen-2/preview-version/discard")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-2"))
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL
    assert view["has_candidate_preview"] is False


# --------------------------------------------------------------------------- #
# 8 + 10. Failure preserves V1; official_publish_ready=false throughout.
# --------------------------------------------------------------------------- #


def test_failure_during_attached_regeneration_preserves_v1(monkeypatch) -> None:
    def _boom(task, *, material_assets=None):
        raise auto.AutoPreviewValidationError("final_video_too_small")
    monkeypatch.setattr(auto, "build_matrix_script_regeneration_payload", _boom)
    repo = _Repo()
    repo.create(_task({INTENT_KEY: _attached_intents()}))

    status = auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-2"), repo)
    assert status["status"] == auto.STATUS_FAILED
    cfg = repo.get("ms-regen-2")["config"]
    # V1 untouched; no V2 candidate written.
    assert cfg["matrix_script_staged_candidate"]["preview_url"] == V1_URL
    assert cfg.get(auto.PREVIEW_VERSIONS_KEY, {}) == {}

    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-2"))
    assert view["regeneration"]["status"] == auto.STATUS_FAILED
    assert view["main_result"]["operator_usable"] is True
    assert view["main_result"]["official_publish_ready"] is False


def test_official_publish_ready_false_throughout(monkeypatch) -> None:
    _stub_regen(monkeypatch)
    repo = _Repo()
    repo.create(_task({INTENT_KEY: _attached_intents()}))
    client = _client(monkeypatch, repo)
    try:
        assert client.post("/api/matrix-script/ms-regen-2/regenerate-preview").json()["official_publish_ready"] is False
        auto.trigger_matrix_script_preview_regeneration(repo.get("ms-regen-2"), repo)
        st = client.get("/api/matrix-script/ms-regen-2/regeneration-status").json()
        assert st["official_publish_ready"] is False
        assert st["has_candidate_preview"] is True
    finally:
        app.dependency_overrides.clear()
    view = owv.build_matrix_script_operator_workbench_view(repo.get("ms-regen-2"))
    assert view["delivery"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# 11. No provider/artifact/raw-manifest/publish/Akool leakage in the projection.
# --------------------------------------------------------------------------- #


def test_no_leakage_in_v2_material_projection() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot()})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    blob = str(owv._scrub_operator_notes(view)).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob
    # new_preview surfaces only operator-safe fields.
    assert set(view["new_preview"].keys()) == {
        "version", "role", "label_zh", "preview_url", "based_on_intents", "source",
        "based_on_assets", "material_bytes_consumed", "material_usage_note_zh",
        # P1-3 PR-D adds the consumed-bytes projection (operator-safe).
        "consumed_materials",
    }
    asset_keys = set(view["new_preview"]["based_on_assets"][0].keys())
    assert asset_keys == {"shot_id", "shot_label_zh", "material_name", "material_kind", "material_kind_label_zh"}
    # material_ref (the raw handle) is NOT surfaced in the operator projection.
    assert "material_ref" not in asset_keys

"""Matrix Script P1-3 PR-D — Regenerate Consumes Uploaded Material Bytes.

PR-C made an operator-uploaded shot material resolvable (``msmaterial://`` →
local_workspace bytes) WITHOUT consuming it. PR-D wires the regeneration path so
a V2 candidate actually CONSUMES those bytes:

  - the regen resolver now resolves a stored ``msmaterial://`` handle to its
    local byte path (``asset://`` references still resolve to nothing);
  - the renderer uses an uploaded image directly, and an uploaded video's first
    frame (extracted via ffmpeg) — anything that does not resolve / cannot be
    consumed falls back to the default asset and is reported NOT consumed;
  - ``material_bytes_consumed`` is true ONLY when at least one uploaded file was
    actually used; the V2 entry records ``consumed_materials`` (shot_id /
    material_name / material_kind / safe ``msmaterial://`` handle / source);
  - the workbench copy is honest: used bytes → "已使用运营上传素材生成新预览";
    unresolved/unsupported → "已绑定运营素材引用，当前预览以素材引用标记生成。".

State rules preserved: V1 stays current main until confirm; V2 is a candidate
only; confirm switches current_main_version=V2 and delivery follows it; discard
and regeneration failure preserve V1; ``official_publish_ready`` stays false.

Boundary: Matrix-Script-scoped only — no Akool live, no provider switching, no
``artifact_storage.py`` / schema-contract surface, no Hot Follow / Digital
Anchor, no official publish, no public publish URL.
"""
from __future__ import annotations

import os
import types
from typing import Any, Dict, Optional

from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import shot_material_storage as storage
from gateway.app.services.matrix_script import tomato_real_result_orchestrator as orch

INTENT_KEY = owv.MATERIAL_INTENT_KEY
TID = "ms-regen-d"
V1_URL = "/api/matrix-script/%s/tomato-real-result/preview/final.mp4" % TID
V2_URL = "/api/matrix-script/%s/preview-version/V2/final.mp4" % TID


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


def _task(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config: Dict[str, Any] = {"matrix_script_staged_candidate": _v1_payload()}
    if extra:
        config.update(extra)
    return {"task_id": TID, "kind": "matrix_script", "config": config}


def _store(monkeypatch, tmp_path, shot_id: str, filename: str, data: bytes, kind: str):
    """Persist a real shot material file and return its StoredShotMaterial."""
    monkeypatch.setattr(
        storage, "get_settings", lambda: types.SimpleNamespace(workspace_root=str(tmp_path))
    )
    return storage.store_shot_material_bytes(
        task_id=TID, shot_id=shot_id, filename=filename, data=data, declared_kind=kind,
    )


def _uploaded_intent(stored, intent: str) -> Dict[str, Any]:
    return {
        "intent": intent,
        "updated_at": "x",
        "material_ref": stored.material_ref,
        "material_name": stored.material_name,
        "material_kind": stored.material_kind,
        "material_source": "operator_upload",
        "storage_scope": "local_workspace",
        "local_path": stored.local_path,
        "bytes_resolvable": True,
    }


# --------------------------------------------------------------------------- #
# 1. Uploaded msmaterial:// handle resolves; overrides built from uploads only.
# --------------------------------------------------------------------------- #


def test_uploaded_msmaterial_handle_resolves_to_bytes(monkeypatch, tmp_path) -> None:
    stored = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    path = auto.resolve_material_asset_bytes_path(stored.material_ref)
    assert path is not None and os.path.exists(path)
    # asset:// references still carry no resolvable bytes.
    assert auto.resolve_material_asset_bytes_path("asset://matrix_script/x/shot05/a1") is None


def test_overrides_built_only_for_resolvable_uploads(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    task = _task({INTENT_KEY: {
        "shot05": _uploaded_intent(img, "replace"),
        # asset:// attachment (PR-A) — dirty + has a ref, but no resolvable bytes.
        "shot04": {"intent": "supplement", "updated_at": "x",
                   "material_ref": "asset://matrix_script/%s/shot04/a1" % TID,
                   "material_name": "番茄特写", "material_kind": "video",
                   "material_source": "operator_attachment"},
    }})
    assets = auto._material_attachment_assets(task)
    overrides = auto._material_overrides_from_assets(assets)
    assert set(overrides.keys()) == {"shot05"}
    assert overrides["shot05"]["material_kind"] == "image"
    assert overrides["shot05"]["material_source"] == "operator_upload"
    assert os.path.exists(overrides["shot05"]["local_path"])


# --------------------------------------------------------------------------- #
# 2. Renderer source resolution: image used directly; video → first frame or
#    honest unsupported fallback (never claims bytes it did not use).
# --------------------------------------------------------------------------- #


def test_image_override_is_used_directly(tmp_path) -> None:
    img = tmp_path / "up.png"
    img.write_bytes(b"\x89PNG" + b"0" * 80)
    default = str(tmp_path / "default.png")
    overrides = {"shot05": {"local_path": str(img), "material_kind": "image"}}
    src, consumed = orch._resolve_shot_render_source("shot05", default, overrides, str(tmp_path))
    assert src == str(img) and consumed is True


def test_video_override_uses_first_frame_when_supported(monkeypatch, tmp_path) -> None:
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"\x00\x00\x00\x18ftyp" + b"0" * 200)
    frame = str(tmp_path / "shot04_material_frame.png")
    monkeypatch.setattr(orch, "_extract_first_video_frame", lambda *a, **k: frame)
    overrides = {"shot04": {"local_path": str(vid), "material_kind": "video"}}
    src, consumed = orch._resolve_shot_render_source("shot04", "default.png", overrides, str(tmp_path))
    assert src == frame and consumed is True


def test_video_override_unsupported_is_honest(monkeypatch, tmp_path) -> None:
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"\x00\x00\x00\x18ftyp" + b"0" * 200)
    # Renderer cannot extract a frame → falls back to default, NOT consumed.
    monkeypatch.setattr(orch, "_extract_first_video_frame", lambda *a, **k: None)
    overrides = {"shot04": {"local_path": str(vid), "material_kind": "video"}}
    src, consumed = orch._resolve_shot_render_source("shot04", "default.png", overrides, str(tmp_path))
    assert src == "default.png" and consumed is False


def test_override_with_missing_bytes_not_consumed(tmp_path) -> None:
    overrides = {"shot05": {"local_path": str(tmp_path / "gone.png"), "material_kind": "image"}}
    src, consumed = orch._resolve_shot_render_source("shot05", "default.png", overrides, str(tmp_path))
    assert src == "default.png" and consumed is False


# --------------------------------------------------------------------------- #
# 3 + 4 + 5. Trigger records consumed_materials / material_bytes_consumed only
#    for shots the renderer actually consumed.
# --------------------------------------------------------------------------- #


def _stub_regen(monkeypatch, consumed_shot_ids) -> None:
    def _fake(task, *, material_assets=None):
        payload = _v2_candidate_payload()
        payload["consumed_material_shot_ids"] = list(consumed_shot_ids)
        return payload

    monkeypatch.setattr(auto, "build_matrix_script_regeneration_payload", _fake)


def test_material_bytes_consumed_true_only_when_used(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    vid = _store(monkeypatch, tmp_path, "shot04", "clip.mp4", b"\x00\x00\x00\x18ftyp" + b"0" * 80, "video")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {
        "shot04": _uploaded_intent(vid, "supplement"),
        "shot05": _uploaded_intent(img, "replace"),
    }}))
    # Renderer reports it consumed only the image shot (video unsupported here).
    _stub_regen(monkeypatch, ["shot05"])
    status = auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    assert status["status"] == auto.STATUS_SUCCEEDED

    v2 = repo.get(TID)["config"][auto.PREVIEW_VERSIONS_KEY]["V2"]
    assert v2["material_bytes_consumed"] is True
    # consumed_materials records ONLY the actually-used shot, with safe handle.
    cm = {m["shot_id"]: m for m in v2["consumed_materials"]}
    assert set(cm) == {"shot05"}
    assert cm["shot05"]["material_name"] == "frame.png"
    assert cm["shot05"]["material_kind"] == "image"
    assert cm["shot05"]["material_ref"].startswith("msmaterial://")
    assert cm["shot05"]["material_source"] == "operator_upload"
    # based_on_assets still records every dirty attached shot.
    assert {a["shot_id"] for a in v2["based_on_assets"]} == {"shot04", "shot05"}
    # The carrier key never persists into the stored payload.
    assert "consumed_material_shot_ids" not in v2["payload"]


def test_material_bytes_consumed_false_when_nothing_used(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))
    _stub_regen(monkeypatch, [])  # renderer consumed nothing
    auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    v2 = repo.get(TID)["config"][auto.PREVIEW_VERSIONS_KEY]["V2"]
    assert v2["material_bytes_consumed"] is False
    assert v2["consumed_materials"] == []


# --------------------------------------------------------------------------- #
# 6. Workbench V2 copy is honest (used vs reference).
# --------------------------------------------------------------------------- #


def _v2_slot(*, consumed: bool, source: str = "operator_upload") -> Dict[str, Any]:
    consumed_materials = (
        [{"shot_id": "shot05", "material_name": "frame.png", "material_kind": "image",
          "material_ref": "msmaterial://%s/shot05/frame.png" % TID, "material_source": source}]
        if consumed else []
    )
    return {"V2": {
        "role": "candidate_preview", "preview_url": V2_URL, "created_at": "x",
        "source": "material_regeneration", "based_on_intents": ["shot05"],
        "based_on_assets": [
            {"shot_id": "shot05", "material_ref": "msmaterial://%s/shot05/frame.png" % TID,
             "material_name": "frame.png", "material_kind": "image"},
        ],
        "material_bytes_consumed": consumed,
        "consumed_materials": consumed_materials,
        "payload": _v2_candidate_payload()}}


def test_view_upload_consumed_copy(monkeypatch, tmp_path) -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=True)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    np = view["new_preview"]
    assert np["material_bytes_consumed"] is True
    assert np["material_usage_note_zh"] == "已使用运营上传素材生成新预览"
    cm = np["consumed_materials"]
    assert cm[0]["shot_id"] == "shot05"
    assert cm[0]["material_ref"].startswith("msmaterial://")
    # local_path is never projected.
    assert "local_path" not in cm[0]


def test_view_reference_copy_when_not_consumed() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=False)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    np = view["new_preview"]
    assert np["material_bytes_consumed"] is False
    assert np["material_usage_note_zh"] == "已绑定运营素材引用，当前预览以素材引用标记生成。"
    assert np["consumed_materials"] == []


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


def test_workbench_renders_upload_consumed_copy_and_list() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=True)})
    view = owv.build_matrix_script_operator_workbench_view(task)
    html = _render_ms_primary_branch(view)
    assert "已使用运营上传素材生成新预览" in html
    assert 'data-role="ms-regen-consumed-materials"' in html
    assert 'data-role="ms-regen-consumed-material"' in html
    # Honest: never a real-pixel-replacement claim, never a raw local path.
    assert "真实替换画面" not in html
    assert "/Users/" not in html and ".local_path" not in html


# --------------------------------------------------------------------------- #
# 7 + 8 + 9 + 10. State rules: V1 protected; confirm→V2; discard/failure keep V1.
# --------------------------------------------------------------------------- #


def test_v1_current_and_delivery_before_confirm(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))
    _stub_regen(monkeypatch, ["shot05"])
    auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    view = owv.build_matrix_script_operator_workbench_view(repo.get(TID))
    assert view["current_main_version"] == "V1"
    assert view["delivery"]["preview_url"] == V1_URL
    assert view["delivery"]["official_publish_ready"] is False


def test_confirm_switches_main_and_delivery_to_v2(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))
    _stub_regen(monkeypatch, ["shot05"])
    auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    result = auto.confirm_matrix_script_preview_version(repo.get(TID), repo)
    assert result == {"ok": True, "current_main_version": "V2"}
    cfg = repo.get(TID)["config"]
    assert cfg["matrix_script_staged_candidate"]["preview_url"] == V2_URL
    assert cfg["matrix_script_staged_candidate"]["official_publish_ready"] is False
    view = owv.build_matrix_script_operator_workbench_view(repo.get(TID))
    assert view["delivery"]["preview_url"] == V2_URL
    assert view["delivery"]["official_publish_ready"] is False


def test_discard_preserves_v1(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))
    _stub_regen(monkeypatch, ["shot05"])
    auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    auto.discard_matrix_script_preview_candidate(repo.get(TID), repo)
    cfg = repo.get(TID)["config"]
    assert cfg["matrix_script_staged_candidate"]["preview_url"] == V1_URL
    assert not cfg.get(auto.PREVIEW_VERSIONS_KEY)


def test_regeneration_failure_preserves_v1(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))

    def _boom(task, *, material_assets=None):
        raise auto.TomatoRealResultError("render exploded")

    monkeypatch.setattr(auto, "build_matrix_script_regeneration_payload", _boom)
    status = auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    assert status["status"] == auto.STATUS_FAILED
    cfg = repo.get(TID)["config"]
    # V1 untouched, no V2 candidate, no consumed flag.
    assert cfg["matrix_script_staged_candidate"]["preview_url"] == V1_URL
    assert not cfg.get(auto.PREVIEW_VERSIONS_KEY)


# --------------------------------------------------------------------------- #
# 11 + 12. official_publish_ready stays false; no leakage in projection.
# --------------------------------------------------------------------------- #


def test_official_publish_ready_false_throughout(monkeypatch, tmp_path) -> None:
    img = _store(monkeypatch, tmp_path, "shot05", "frame.png", b"\x89PNG" + b"0" * 80, "image")
    repo = _Repo()
    repo.create(_task({INTENT_KEY: {"shot05": _uploaded_intent(img, "replace")}}))
    _stub_regen(monkeypatch, ["shot05"])
    status = auto.trigger_matrix_script_preview_regeneration(repo.get(TID), repo)
    assert status["official_publish_ready"] is False
    v2 = repo.get(TID)["config"][auto.PREVIEW_VERSIONS_KEY]["V2"]
    assert v2["payload"]["official_publish_ready"] is False


def test_no_leakage_with_consumed_upload_projection() -> None:
    task = _task({auto.PREVIEW_VERSIONS_KEY: _v2_slot(consumed=True)})
    view = owv.build_matrix_script_operator_workbench_view(task)  # must not raise
    blob = str(owv._scrub_operator_notes(view)).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob

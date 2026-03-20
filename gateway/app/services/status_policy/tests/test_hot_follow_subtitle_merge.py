from pathlib import Path
import sys
import types

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services.hot_follow_subtitles import merge_target_srt


def test_merge_target_srt_keeps_existing_segments_and_appends_later_ranges():
    base = (
        "1\n00:00:00,000 --> 00:00:02,000\n早段一\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\n早段二\n"
    )
    overlay = "1\n00:00:08,000 --> 00:00:10,000\n后段三\n"

    merged = merge_target_srt(base, overlay)

    assert "早段一" in merged
    assert "早段二" in merged
    assert "后段三" in merged
    assert "00:00:08,000 --> 00:00:10,000" in merged


def test_sync_saved_target_subtitle_artifact_reuploads_saved_text_even_when_mm_srt_exists(monkeypatch, tmp_path):
    artifact_store = {"deliver/tasks/hf-sync/mm.srt": "stale"}

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        key = f"deliver/tasks/{task_id}/{artifact_name}"
        artifact_store[key] = Path(local_path).read_text(encoding="utf-8")
        return key

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in artifact_store)
    monkeypatch.setattr(hf_router, "object_head", lambda key: {"ContentLength": str(len(artifact_store[str(key)])), "Content-Type": "application/octet-stream"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")))

    saved_text = "1\n00:00:08,000 --> 00:00:10,000\n新字幕\n"
    task = {"task_id": "hf-sync", "mm_srt_path": "deliver/tasks/hf-sync/mm.srt"}

    key = hf_router._hf_sync_saved_target_subtitle_artifact("hf-sync", task, saved_text=saved_text)

    assert key == "deliver/tasks/hf-sync/mm.srt"
    assert artifact_store["deliver/tasks/hf-sync/mm.srt"].strip() == saved_text.strip()


def test_patch_hot_follow_subtitles_persists_merged_target_srt_for_dub_and_compose(monkeypatch, tmp_path):
    artifact_store: dict[str, str] = {}
    existing_target = "1\n00:00:00,000 --> 00:00:02,000\n早段一\n"
    later_overlay = "1\n00:00:08,000 --> 00:00:10,000\n后段二\n"

    class _Repo:
        def __init__(self):
            self.task = {"task_id": "hf-merge", "kind": "hot_follow", "subtitles_status": "pending"}

        def get(self, task_id):
            assert task_id == "hf-merge"
            return dict(self.task)

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    repo = _Repo()
    override_path = tmp_path / "hf-merge" / "override.srt"
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(existing_target, encoding="utf-8")

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        key = f"deliver/tasks/{task_id}/{artifact_name}"
        artifact_store[key] = Path(local_path).read_text(encoding="utf-8")
        return key

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda _task_id: override_path)
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in artifact_store)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: artifact_store[str(key)].encode("utf-8") if str(key) in artifact_store else b"")
    monkeypatch.setattr(hf_router, "object_head", lambda key: {"ContentLength": str(len(artifact_store[str(key)])), "Content-Type": "application/octet-stream"} if str(key) in artifact_store else None)
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")) if meta else (0, None))
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_policy_upsert", lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates))

    payload = hf_router.HotFollowSubtitlesRequest(srt_text=later_overlay)
    result = hf_router.patch_hot_follow_subtitles("hf-merge", payload, repo=repo)

    merged = result["subtitles"]["srt_text"]
    mm_key = "deliver/tasks/hf-merge/mm.srt"

    assert "早段一" in merged
    assert "后段二" in merged
    assert repo.task["mm_srt_path"] == mm_key
    assert artifact_store[mm_key].strip() == merged.strip()
    assert hf_router._hf_dub_input_text("hf-merge", repo.task) == merged
    assert hf_router._resolve_target_srt_key(repo.task, "hf-merge", "mm") == mm_key

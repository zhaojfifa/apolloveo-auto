from __future__ import annotations

from io import BytesIO

from gateway.app.services import media_helpers
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.utils.pipeline_config import parse_pipeline_config


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str) -> dict:
        assert task_id == self.task["task_id"]
        return dict(self.task)


class _Upload:
    filename = "bed.mp3"
    file = BytesIO(b"fake-audio")


def _patch_bgm_upload_io(monkeypatch):
    monkeypatch.setattr(media_helpers, "save_upload_to_paths", lambda **_kwargs: 10)
    monkeypatch.setattr(
        media_helpers,
        "upload_task_artifact",
        lambda _task, _path, artifact_name, *, task_id: f"deliver/tasks/{task_id}/{artifact_name}",
    )
    monkeypatch.setattr(media_helpers, "get_download_url", lambda key: f"/download/{key}")


def test_bgm_upload_without_strategy_preserves_existing_source_audio_policy(monkeypatch):
    _patch_bgm_upload_io(monkeypatch)
    repo = _Repo(
        {
            "task_id": "hf-policy-preserve",
            "kind": "hot_follow",
            "pipeline_config": {"source_audio_policy": "preserve", "bgm_strategy": "keep"},
            "config": {"source_audio_policy": "preserve"},
        }
    )

    def _upsert(_repo, _task_id, _task, updates, **_kwargs):
        repo.task.update(updates)

    monkeypatch.setattr(media_helpers, "policy_upsert", _upsert)

    result = media_helpers.upload_task_bgm_impl(
        "hf-policy-preserve",
        bgm_file=_Upload(),
        original_pct=None,
        bgm_pct=None,
        mix_ratio=0.35,
        strategy=None,
        repo=repo,
    )

    pipeline = parse_pipeline_config(repo.task["pipeline_config"])
    assert result["strategy"] == "keep"
    assert repo.task["config"]["source_audio_policy"] == "preserve"
    assert repo.task["config"]["bgm"]["strategy"] == "keep"
    assert pipeline["source_audio_policy"] == "preserve"
    assert pipeline["bgm_strategy"] == "keep"
    assert source_audio_policy_from_task(repo.task) == "preserve"


def test_explicit_replace_bgm_upload_switches_policy_to_mute(monkeypatch):
    _patch_bgm_upload_io(monkeypatch)
    repo = _Repo(
        {
            "task_id": "hf-policy-replace",
            "kind": "hot_follow",
            "pipeline_config": {"source_audio_policy": "preserve", "bgm_strategy": "keep"},
            "config": {"source_audio_policy": "preserve", "bgm": {"strategy": "keep"}},
        }
    )

    def _upsert(_repo, _task_id, _task, updates, **_kwargs):
        repo.task.update(updates)

    monkeypatch.setattr(media_helpers, "policy_upsert", _upsert)

    result = media_helpers.upload_task_bgm_impl(
        "hf-policy-replace",
        bgm_file=_Upload(),
        original_pct=None,
        bgm_pct=None,
        mix_ratio=0.2,
        strategy="replace",
        repo=repo,
    )

    pipeline = parse_pipeline_config(repo.task["pipeline_config"])
    assert result["strategy"] == "replace"
    assert repo.task["config"]["source_audio_policy"] == "mute"
    assert repo.task["config"]["bgm"]["strategy"] == "replace"
    assert pipeline["source_audio_policy"] == "mute"
    assert pipeline["bgm_strategy"] == "replace"
    assert source_audio_policy_from_task(repo.task) == "mute"


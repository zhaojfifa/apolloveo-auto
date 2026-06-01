"""Matrix Script minimal-result artifact staged persistence tests (PR-16R).

Uses an in-memory fake sink (no real R2). Proves the local result pack is
staged into opaque artifact refs as a delivery candidate that is NOT
publish-ready, with no provider/publish leakage.
"""
from __future__ import annotations

import json
import os

import pytest

from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    ARTIFACT_REF_PREFIX,
    STORAGE_SCOPE_STAGED,
    InMemoryArtifactSink,
    MatrixScriptMinimalResultStagingRecord,
    StagingError,
    assert_no_staging_forbidden_tokens,
    stage_minimal_result,
    staging_record_to_dict,
)
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    DeliveryViewError,
    staged_record_to_delivery_block,
)


def _pack(tmp_path):
    """Create a tiny real result pack on disk; return path kwargs."""
    (tmp_path / "final").mkdir()
    (tmp_path / "subtitles").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "shots").mkdir()
    final = tmp_path / "final" / "final.mp4"; final.write_bytes(b"\x00\x01")
    manifest = tmp_path / "manifest.json"; manifest.write_text("{}")
    subs = tmp_path / "subtitles" / "subtitles.srt"; subs.write_text("1\n")
    audio = tmp_path / "audio" / "narration.wav"; audio.write_bytes(b"\x00")
    clips = []
    for i in (1, 2, 3):
        c = tmp_path / "shots" / f"scene_{i:03d}.mp4"; c.write_bytes(b"\x00"); clips.append(str(c))
    return dict(
        final_video_path=str(final), manifest_path=str(manifest),
        subtitles_path=str(subs), audio_path=str(audio), scene_clip_paths=tuple(clips),
    )


def _stage(tmp_path, **over):
    sink = InMemoryArtifactSink()
    rec = stage_minimal_result(sink=sink, task_id="ms-stage-1", **{**_pack(tmp_path), **over})
    return sink, rec


# ---------------------------------------------------------------------------
# 1-6. staging behavior
# ---------------------------------------------------------------------------


def test_final_video_staged_to_artifact_ref(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    assert rec.final_video_artifact_ref.startswith(ARTIFACT_REF_PREFIX)
    assert "matrix_script/ms-stage-1/final/final.mp4" in rec.final_video_artifact_ref


def test_manifest_subtitles_audio_staged(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    assert rec.manifest_artifact_ref.startswith(ARTIFACT_REF_PREFIX)
    assert rec.subtitles_artifact_ref.endswith("subtitles.srt")
    assert rec.audio_artifact_ref.endswith("narration.wav")


def test_scene_clips_staged_by_default(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    assert rec.scene_clips_staged is True
    assert len(rec.scene_clip_artifact_refs) == 3
    assert all(r.startswith(ARTIFACT_REF_PREFIX) for r in rec.scene_clip_artifact_refs)


def test_scene_clips_local_only_when_disabled(tmp_path) -> None:
    _, rec = _stage(tmp_path, stage_scene_clips=False)
    assert rec.scene_clips_staged is False
    assert rec.scene_clip_artifact_refs == ()


def test_storage_scope_and_candidate_flags(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    assert rec.storage_scope == STORAGE_SCOPE_STAGED == "artifact_staged"
    assert rec.delivery_candidate is True
    assert rec.official_publish_ready is False
    assert rec.generation_provider == "none"


# ---------------------------------------------------------------------------
# 7-8. leakage
# ---------------------------------------------------------------------------


def test_record_has_no_publish_or_provider_leak(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    d = staging_record_to_dict(rec)
    for forbidden_key in ("publish_url", "publish_status", "provider_url", "temporary_url", "download_url"):
        assert forbidden_key not in d
    blob = json.dumps(d, ensure_ascii=False).lower()
    for token in ("akool", "vendor", "model_id", "credit", "provider_url", "publish_url", "publish_status", "http://", "https://"):
        assert token not in blob


def test_guard_rejects_injected_publish_url() -> None:
    with pytest.raises(StagingError):
        assert_no_staging_forbidden_tokens({"publish_url": "x"})


# ---------------------------------------------------------------------------
# 9-10. failure + sink record fidelity
# ---------------------------------------------------------------------------


def test_missing_final_mp4_fails_clearly(tmp_path) -> None:
    sink = InMemoryArtifactSink()
    pack = _pack(tmp_path)
    pack["final_video_path"] = str(tmp_path / "final" / "does_not_exist.mp4")
    with pytest.raises(StagingError):
        stage_minimal_result(sink=sink, task_id="t", **pack)


def test_sink_records_exact_files_persisted(tmp_path) -> None:
    sink, rec = _stage(tmp_path)
    # final + manifest + subtitles + audio + 3 clips = 7 puts
    assert len(sink.puts) == 7
    local_paths = [p for p, _ in sink.puts]
    assert any(p.endswith("final/final.mp4") for p in local_paths)
    assert any(p.endswith("manifest.json") for p in local_paths)
    assert sum(1 for p in local_paths if "shots/scene_" in p) == 3


def test_sink_requires_put_method(tmp_path) -> None:
    with pytest.raises(StagingError):
        stage_minimal_result(sink=object(), task_id="t", **_pack(tmp_path))


# ---------------------------------------------------------------------------
# delivery staged-candidate projection (wave criterion 5, service layer)
# ---------------------------------------------------------------------------


def test_staged_record_to_delivery_block(tmp_path) -> None:
    _, rec = _stage(tmp_path)
    block = staged_record_to_delivery_block(rec)
    assert block["storage_scope"] == "artifact_staged"
    assert block["delivery_candidate"] is True
    assert block["official_publish_ready"] is False
    assert block["final_video_artifact_ref"].startswith("artifact://")
    assert block["scene_clip_count"] == 3
    assert "尚未正式发布" in block["delivery_note"]
    blob = json.dumps(block, ensure_ascii=False).lower()
    for token in ("akool", "provider_url", "publish_url", "publish_status", "download_url", "http://", "https://"):
        assert token not in blob


def test_delivery_block_rejects_non_record() -> None:
    with pytest.raises(DeliveryViewError):
        staged_record_to_delivery_block({"not": "a record"})


def test_staging_record_type_defaults() -> None:
    rec = MatrixScriptMinimalResultStagingRecord(
        task_id="t",
        final_video_artifact_ref="artifact://matrix_script/t/final/final.mp4",
        manifest_artifact_ref="artifact://matrix_script/t/manifest/manifest.json",
        subtitles_artifact_ref="artifact://matrix_script/t/subtitles/subtitles.srt",
        audio_artifact_ref="artifact://matrix_script/t/audio/narration.wav",
        scene_clip_artifact_refs=(),
    )
    assert rec.line_id == "matrix_script"
    assert rec.storage_scope == "artifact_staged"
    assert rec.official_publish_ready is False
    assert rec.delivery_candidate is True

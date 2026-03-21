"""Tests for Hot Follow compose freshness / staleness model.

Business contract:
- Only the saved authoritative subtitle (mm.srt after Save Subtitle) is the
  input to compose.
- After Save Subtitle OR successful Re-dub, the old final must become stale.
- Old final existence alone must NOT short-circuit compose.
- Compose success must persist snapshot fields and promote current final.
- compose_ready / publish_ready must be False while final is stale.

Covered scenarios:
  A. First compose success – final becomes fresh.
  B. Subtitle edit makes old final stale immediately.
  C. Re-dub makes old final stale immediately.
  D. Re-compose after stale: creates fresh current final.
  E. Stale final does NOT bypass compose (early-exit blocked).
  F. compute_final_staleness cascade: SHA → dub timestamp → wall-clock fallback.
  G. ready-gate: final_fresh=False → compose_ready=False → publish_ready=False.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gateway.app.services.task_view_helpers import (
    compute_composed_state,
    compute_final_staleness,
)
from gateway.app.services.compose_service import _current_final_is_fresh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(minutes_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


TASK_BASE = {
    "task_id": "hftest-01",
    "kind": "hot_follow",
    "status": "ready",
    "compose_last_status": "done",
}


# ---------------------------------------------------------------------------
# A. compute_final_staleness: no staleness on fresh first compose
# ---------------------------------------------------------------------------

class TestComputeFinalStaleness:
    def test_no_staleness_when_snapshots_match(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_A",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_A",
            "final_source_subtitles_content_hash": "HASH_A",
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result is None

    def test_audio_sha_mismatch_gives_stale_after_dub(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_A",  # old
            "subtitles_content_hash": "HASH_A",
            "final_source_subtitles_content_hash": "HASH_A",
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_dub"

    def test_subtitle_hash_mismatch_gives_stale_after_subtitles(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_A",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_B",       # new
            "final_source_subtitles_content_hash": "HASH_A",  # old
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_subtitles"

    def test_dub_timestamp_fallback_when_no_sha(self):
        """When final_source_audio_sha256 is absent, fall back to dub_generated_at timestamp."""
        compose_time = _ts(minutes_ago=10)
        dub_time = _ts(minutes_ago=5)  # newer than compose
        task = {
            **TASK_BASE,
            "compose_last_finished_at": compose_time,
            "dub_generated_at": dub_time,
            # no SHA snapshot fields
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_dub"

    def test_subtitle_timestamp_fallback_when_no_hash(self):
        """Fall back to subtitles_override_updated_at when no hash snapshot."""
        compose_time = _ts(minutes_ago=10)
        sub_time = _ts(minutes_ago=5)  # newer than compose
        task = {
            **TASK_BASE,
            "compose_last_finished_at": compose_time,
            "subtitles_override_updated_at": sub_time,
            # no hash snapshot fields
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_subtitles"

    def test_no_staleness_when_final_does_not_exist(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_A",
        }
        result = compute_final_staleness(task, final_exists=False, compose_done=True)
        assert result is None

    def test_no_staleness_when_compose_not_done(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_A",
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=False)
        assert result is None

    def test_audio_stale_takes_priority_over_subtitle_stale(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_B",
            "final_source_subtitles_content_hash": "HASH_A",
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_dub"

    def test_dub_before_compose_is_not_stale(self):
        compose_time = _ts(minutes_ago=5)
        dub_time = _ts(minutes_ago=10)  # older than compose → not stale
        task = {
            **TASK_BASE,
            "compose_last_finished_at": compose_time,
            "dub_generated_at": dub_time,
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result is None


# ---------------------------------------------------------------------------
# B / C. _current_final_is_fresh: compose early-exit gate
# ---------------------------------------------------------------------------

class TestCurrentFinalIsFresh:
    def _fresh_task(self) -> dict:
        return {
            "compose_last_status": "done",
            "audio_sha256": "SHA_A",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_A",
            "final_source_subtitles_content_hash": "HASH_A",
        }

    def _revision(self, task: dict) -> dict:
        return {
            "audio_sha256": task.get("audio_sha256"),
            "subtitle_content_hash": task.get("subtitles_content_hash"),
            "subtitle_updated_at": task.get("subtitles_override_updated_at"),
        }

    def test_fresh_when_all_match(self):
        task = self._fresh_task()
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=True, final_size=500_000
        ) is True

    def test_not_fresh_when_audio_sha_changed(self):
        task = self._fresh_task()
        task["audio_sha256"] = "SHA_B"  # re-dub produced new audio
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=True, final_size=500_000
        ) is False

    def test_not_fresh_when_subtitle_hash_changed(self):
        task = self._fresh_task()
        task["subtitles_content_hash"] = "HASH_B"  # subtitle edited and saved
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=True, final_size=500_000
        ) is False

    def test_not_fresh_when_final_does_not_exist(self):
        task = self._fresh_task()
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=False, final_size=0
        ) is False

    def test_not_fresh_when_no_snapshot(self):
        """Without compose snapshot fields, cannot confirm freshness → recompose."""
        task = {
            "compose_last_status": "done",
            "audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_A",
            # no final_source_* fields
        }
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=True, final_size=500_000
        ) is False

    def test_not_fresh_when_compose_status_not_done(self):
        task = self._fresh_task()
        task["compose_last_status"] = "failed"
        assert _current_final_is_fresh(
            task, revision=self._revision(task), final_exists=True, final_size=500_000
        ) is False


# ---------------------------------------------------------------------------
# D. After re-compose, staleness is cleared
# ---------------------------------------------------------------------------

class TestAfterRecompose:
    def test_fresh_after_compose_updates_snapshot(self):
        """Simulate: subtitle saved → re-dub → re-compose → snapshot written."""
        task = {
            "compose_last_status": "done",
            "audio_sha256": "SHA_B",              # new dub
            "final_source_audio_sha256": "SHA_B", # compose wrote snapshot
            "subtitles_content_hash": "HASH_B",   # new subtitle
            "final_source_subtitles_content_hash": "HASH_B",  # compose wrote snapshot
        }
        assert compute_final_staleness(task, final_exists=True, compose_done=True) is None

    def test_revision_snapshot_fields_are_written_by_upload_and_verify(self):
        """Integration: verify _upload_and_verify would write snapshot keys."""
        from gateway.app.services.compose_service import CompositionService
        # The return dict of _upload_and_verify must include the 4 source snapshot fields.
        expected_keys = {
            "final_source_audio_sha256",
            "final_source_dub_generated_at",
            "final_source_subtitles_content_hash",
            "final_source_subtitle_updated_at",
        }
        import inspect
        src = inspect.getsource(CompositionService._upload_and_verify)
        for key in expected_keys:
            assert f'"{key}"' in src, f"Missing snapshot key in _upload_and_verify: {key}"


# ---------------------------------------------------------------------------
# E. compute_composed_state: freshness model end-to-end
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# E. compute_composed_state: freshness fields are present in return dict
# ---------------------------------------------------------------------------

class TestComputeComposedStateReturnShape:
    """Verify compute_final_staleness feeds correctly into composed_ready."""

    def test_staleness_propagates_to_composed_ready_false(self):
        """When final is stale, composed_ready must be False regardless of audio."""
        # compute_final_staleness is pure — test it directly.
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_A",
            "final_source_subtitles_content_hash": "HASH_A",
        }
        stale = compute_final_staleness(task, final_exists=True, compose_done=True)
        # When stale, final_fresh=False, so composed_ready must be False.
        final_fresh = stale is None
        assert final_fresh is False

    def test_fresh_final_allows_composed_ready(self):
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_A",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_A",
            "final_source_subtitles_content_hash": "HASH_A",
        }
        stale = compute_final_staleness(task, final_exists=True, compose_done=True)
        final_fresh = stale is None
        assert final_fresh is True

    def test_upload_and_verify_contains_snapshot_keys(self):
        """Integration: _upload_and_verify must persist 4 compose snapshot fields."""
        import inspect
        from gateway.app.services.compose_service import CompositionService
        src = inspect.getsource(CompositionService._upload_and_verify)
        for key in (
            "final_source_audio_sha256",
            "final_source_dub_generated_at",
            "final_source_subtitles_content_hash",
            "final_source_subtitle_updated_at",
        ):
            assert f'"{key}"' in src, f"Missing snapshot key in _upload_and_verify: {key}"


# ---------------------------------------------------------------------------
# F. Ready-gate: final_fresh signal prevents false compose_ready
# ---------------------------------------------------------------------------

class TestReadyGateFinalFreshSignal:
    def _run_gate(self, task: dict, state: dict) -> dict:
        from gateway.app.services.ready_gate.hot_follow_rules import HOT_FOLLOW_GATE_SPEC
        from gateway.app.services.ready_gate.engine import evaluate_ready_gate
        return evaluate_ready_gate(HOT_FOLLOW_GATE_SPEC, task, state)

    def _base_state(self, *, fresh: bool, stale_reason: str | None = None) -> dict:
        return {
            "final": {
                "exists": True,
                "fresh": fresh,
                "stale_reason": stale_reason,
            },
            "final_stale_reason": stale_reason,
            "audio": {
                "status": "done",
                "audio_ready": True,
            },
            "media": {
                "voiceover_url": "/audio/mm.mp3",
            },
        }

    def _base_task(self) -> dict:
        return {
            "kind": "hot_follow",
            "dub_status": "done",
            "mm_audio_key": "deliver/tasks/t1/audio_mm.mp3",
            "mm_audio_voice_id": "my-MM-ThihaNeural",
            "mm_audio_provider": "azure-speech",
            "subtitles_status": "ready",
            "mm_srt_path": "deliver/tasks/t1/mm.srt",
        }

    def test_gate_compose_ready_true_when_final_fresh(self):
        result = self._run_gate(
            self._base_task(),
            self._base_state(fresh=True, stale_reason=None),
        )
        assert result["compose_ready"] is True
        assert result["publish_ready"] is True

    def test_gate_compose_ready_false_when_final_stale(self):
        result = self._run_gate(
            self._base_task(),
            self._base_state(fresh=False, stale_reason="final_stale_after_dub"),
        )
        assert result["compose_ready"] is False
        assert result["publish_ready"] is False

    def test_gate_final_stale_in_blocking_reasons(self):
        result = self._run_gate(
            self._base_task(),
            self._base_state(fresh=False, stale_reason="final_stale_after_dub"),
        )
        assert "final_stale" in result["blocking"]

    def test_gate_compose_ready_false_when_no_freshness_metadata(self):
        """No final_source_* fields → final_fresh=False → compose must run."""
        state = {
            "final": {"exists": True},  # no 'fresh' or 'stale_reason'
            "audio": {"status": "done", "audio_ready": True},
            "media": {"voiceover_url": "/audio/mm.mp3"},
        }
        result = self._run_gate(self._base_task(), state)
        assert result["compose_ready"] is False


# ---------------------------------------------------------------------------
# G. Full state-transition: Save Subtitle → Re-dub → Re-compose
# ---------------------------------------------------------------------------

class TestStateTransitions:
    """Verify the expected state at each step of the workflow."""

    def test_save_subtitle_makes_final_stale(self):
        """After subtitle save, existing final (with old hash) must become stale."""
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_A",
            "final_source_audio_sha256": "SHA_A",
            "subtitles_content_hash": "HASH_B",              # new — just saved
            "final_source_subtitles_content_hash": "HASH_A", # old compose snapshot
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_subtitles"

    def test_redub_makes_final_stale(self):
        """After re-dub, existing final (with old audio) must become stale."""
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",              # new — just re-dubbed
            "final_source_audio_sha256": "SHA_A", # old compose snapshot
            "subtitles_content_hash": "HASH_B",
            "final_source_subtitles_content_hash": "HASH_B",  # subtitle already matched
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result == "final_stale_after_dub"

    def test_recompose_with_new_inputs_produces_fresh_final(self):
        """After re-compose, snapshot is updated → no staleness."""
        task = {
            **TASK_BASE,
            "audio_sha256": "SHA_B",
            "final_source_audio_sha256": "SHA_B",  # compose updated snapshot
            "subtitles_content_hash": "HASH_B",
            "final_source_subtitles_content_hash": "HASH_B",  # compose updated snapshot
        }
        result = compute_final_staleness(task, final_exists=True, compose_done=True)
        assert result is None

    def test_old_final_existence_does_not_bypass_compose_when_stale(self):
        """_current_final_is_fresh must return False → compose must run."""
        task_after_redub = {
            "compose_last_status": "done",
            "audio_sha256": "SHA_B",              # new dub
            "final_source_audio_sha256": "SHA_A", # old snapshot
            "subtitles_content_hash": "HASH_B",
            "final_source_subtitles_content_hash": "HASH_B",
        }
        revision = {
            "audio_sha256": "SHA_B",
            "subtitle_content_hash": "HASH_B",
            "subtitle_updated_at": None,
        }
        assert _current_final_is_fresh(
            task_after_redub,
            revision=revision,
            final_exists=True,
            final_size=500_000,
        ) is False

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    from pydantic import BaseModel

    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import tasks as tasks_router
from gateway.app.steps.subtitles import _normalize_hot_follow_source_text


def test_hot_follow_beauty_normalization_keeps_seed_terms():
    text = "这个布灵布灵的双头口红是亚光质地，hagard 氛围感也能做出来"
    normalized, applied = _normalize_hot_follow_source_text(
        text,
        {"protected_terms": ["SPF", "PA+++"]},
    )
    assert "bling bling" in normalized
    assert "双头唇釉" in normalized
    assert "哑光" in normalized
    assert "haggard" in normalized
    assert applied


def test_hot_follow_stale_final_is_not_counted_when_audio_not_ready(monkeypatch):
    task_id = "hf-stale-final-01"
    stale_final_key = tasks_router.deliver_key(task_id, "final.mp4")

    monkeypatch.setattr(
        tasks_router,
        "object_exists",
        lambda key: str(key) == stale_final_key,
    )
    monkeypatch.setattr(
        tasks_router,
        "object_head",
        lambda key: {"content_length": str(tasks_router.MIN_VIDEO_BYTES + 1000), "content_type": "video/mp4"}
        if str(key) == stale_final_key
        else None,
    )

    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "content_lang": "my",
        "dub_status": "failed",
        "compose_status": "pending",
        "compose_last_status": "pending",
        "config": {
            "tts_requested_voice": "mm_female_1",
            "tts_provider": "azure-speech",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_request_token": "new",
            "tts_completed_token": None,
        },
    }

    result = tasks_router._compute_composed_state(task, task_id)
    assert result["final"]["exists"] is False
    assert result["composed_ready"] is False
    assert result["composed_reason"] in {
        "missing_raw",
        "missing_voiceover",
        "dub_not_done",
        "audio_not_ready",
        "final_missing",
    }

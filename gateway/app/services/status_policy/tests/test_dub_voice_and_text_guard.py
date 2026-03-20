from pathlib import Path
import sys
from types import SimpleNamespace
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

from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
from gateway.app.services.steps_v1 import _resolve_mm_txt_text
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.tts_policy import normalize_target_lang, resolve_tts_voice


def test_normalize_target_lang_mm_to_my():
    assert normalize_target_lang("mm") == "my"
    assert normalize_target_lang("my") == "my"


def test_resolve_tts_voice_mm_rejects_zh_voice():
    settings = SimpleNamespace(
        edge_tts_voice_map={"mm_female_1": "my-MM-NilarNeural"},
        azure_tts_voice_map={"mm_female_1": "my-MM-NilarNeural"},
        lovo_voice_id_mm="mm_female_1",
    )
    voice, overridden = resolve_tts_voice(
        settings=settings,
        provider="azure-speech",
        target_lang="mm",
        requested_voice="zh-CN-XiaoxiaoNeural",
    )
    assert voice == "my-MM-NilarNeural"
    assert overridden is True


def test_resolve_tts_voice_mm_male_alias_maps_to_provider_voice():
    settings = SimpleNamespace(
        edge_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
        },
        azure_tts_voice_map={},
        lovo_voice_id_mm="mm_female_1",
    )
    voice, overridden = resolve_tts_voice(
        settings=settings,
        provider="edge-tts",
        target_lang="mm",
        requested_voice="mm_male_1",
    )
    assert voice == "my-MM-ThihaNeural"
    assert overridden is True


def test_clean_and_analyze_dub_text_detects_cjk_lines():
    text = """1
00:00:00,000 --> 00:00:01,000
မင်္ဂလာပါ

29
00:00:02,000 --> 00:00:03,000
淡岩星际战神
"""
    out = clean_and_analyze_dub_text(text, "mm")
    assert "detected CJK in mm subtitles" in str(out.get("warning") or "")
    assert 29 in (out.get("cjk_lines") or [])


def test_hot_follow_ready_gate_blocks_when_audio_invalid():
    state = compute_hot_follow_state(
        {"task_id": "t1", "dub_status": "pending", "voice_id": ""},
        {
            "task_id": "t1",
            "audio": {"status": "pending", "tts_voice": "", "voiceover_url": None},
            "final": {"exists": False},
        },
    )
    gate = state.get("ready_gate") or {}
    assert gate.get("compose_ready") is False
    assert gate.get("publish_ready") is False
    assert "audio_not_done" in (gate.get("blocking") or [])
    assert "tts_voice_invalid" in (gate.get("blocking") or [])


def test_hot_follow_reconcile_compose_done_from_final_exists():
    state = compute_hot_follow_state(
        {"task_id": "hf-1", "compose_status": "pending"},
        {
            "task_id": "hf-1",
            "final": {"exists": True},
            "compose": {"last": {"status": "pending"}},
            "audio": {"status": "done", "tts_voice": "my-MM-NilarNeural", "voiceover_url": "/a.mp3", "audio_ready": True},
            "pipeline": [{"key": "compose", "status": "pending", "state": "pending", "message": ""}],
            "media": {},
        },
    )
    gate = state.get("ready_gate") or {}
    assert state.get("compose_status") == "done"
    assert (state.get("compose") or {}).get("last", {}).get("status") == "done"
    assert (state.get("media") or {}).get("final_url") == "/v1/tasks/hf-1/final"
    assert (state.get("final_url") or "") == "/v1/tasks/hf-1/final"
    compose_step = next((x for x in (state.get("pipeline") or []) if x.get("key") == "compose"), {})
    assert compose_step.get("status") == "done"
    assert compose_step.get("state") == "done"
    assert "compose_not_done" not in (gate.get("blocking") or [])


def test_hot_follow_compose_not_done_kept_when_final_missing():
    state = compute_hot_follow_state(
        {"task_id": "hf-2", "compose_status": "pending"},
        {
            "task_id": "hf-2",
            "final": {"exists": False},
            "audio": {"status": "done", "tts_voice": "my-MM-NilarNeural", "voiceover_url": "/a.mp3"},
        },
    )
    gate = state.get("ready_gate") or {}
    assert state.get("compose_status") != "done"
    assert "compose_not_done" in (gate.get("blocking") or [])


def test_hot_follow_final_exists_but_audio_not_ready_stays_blocked():
    state = compute_hot_follow_state(
        {"task_id": "hf-3", "compose_status": "pending"},
        {
            "task_id": "hf-3",
            "final": {"exists": True},
            "compose": {"last": {"status": "pending"}},
            "audio": {"status": "running", "tts_voice": "mm_male_1", "voiceover_url": "/a.mp3", "audio_ready": False},
            "pipeline": [{"key": "compose", "status": "pending", "state": "pending", "message": ""}],
        },
    )
    gate = state.get("ready_gate") or {}
    assert state.get("compose_status") != "done"
    assert gate.get("compose_ready") is False
    assert "audio_not_ready" in (gate.get("blocking") or [])


def test_hot_follow_stale_final_keeps_current_compose_pending():
    state = compute_hot_follow_state(
        {"task_id": "hf-stale", "compose_status": "done"},
        {
            "task_id": "hf-stale",
            "final": {"exists": True, "url": "/v1/tasks/hf-stale/final"},
            "compose": {"last": {"status": "done"}},
            "audio": {
                "status": "done",
                "tts_voice": "my-MM-NilarNeural",
                "voiceover_url": "/v1/tasks/hf-stale/audio_mm",
                "audio_ready": True,
            },
            "pipeline": [{"key": "compose", "status": "done", "state": "done", "message": ""}],
            "deliverables": [{"kind": "final", "status": "done", "state": "done", "url": "/v1/tasks/hf-stale/final"}],
            "final_fresh": False,
        },
    )
    gate = state.get("ready_gate") or {}
    compose_step = next((x for x in (state.get("pipeline") or []) if x.get("key") == "compose"), {})
    final_row = next((x for x in (state.get("deliverables") or []) if x.get("kind") == "final"), {})
    assert state.get("compose_status") == "pending"
    assert (state.get("compose") or {}).get("last", {}).get("status") == "pending"
    assert gate.get("compose_ready") is False
    assert "compose_not_done" in (gate.get("blocking") or [])
    assert compose_step.get("status") == "pending"
    assert final_row.get("status") == "pending"


def test_hot_follow_ready_gate_ignores_no_dub_when_audio_artifact_is_ready():
    state = compute_hot_follow_state(
        {"task_id": "hf-a9", "compose_status": "pending"},
        {
            "task_id": "hf-a9",
            "final": {"exists": False},
            "audio": {
                "status": "done",
                "tts_voice": "my-MM-NilarNeural",
                "voiceover_url": "/v1/tasks/hf-a9/audio_mm",
                "audio_ready": True,
                "no_dub": True,
                "no_dub_reason": "no_speech_detected",
            },
            "subtitles": {
                "subtitle_artifact_exists": True,
                "actual_burn_subtitle_source": "mm.srt",
                "edited_text": "",
                "srt_text": "",
            },
        },
    )
    gate = state.get("ready_gate") or {}
    assert gate.get("subtitle_ready") is True
    assert gate.get("compose_reason") == "compose_not_done"
    assert "no_speech_detected" not in (gate.get("blocking") or [])


def test_resolve_mm_txt_text_prefers_target_subtitle_artifact_over_edited_text():
    resolved, used_fallback, fallback_source = _resolve_mm_txt_text(
        mm_txt_text="no subtitles",
        override_text=None,
        edited_text="旧的编辑区草稿",
        mm_srt_text="1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n",
    )
    assert resolved == "မင်္ဂလာပါ"
    assert used_fallback is True
    assert fallback_source == "mm_srt"


def test_resolve_mm_txt_text_uses_manual_target_override_before_marker():
    resolved, used_fallback, fallback_source = _resolve_mm_txt_text(
        mm_txt_text="no subtitles",
        override_text="မင်္ဂလာပါ",
        edited_text=None,
        mm_srt_text="",
    )
    assert resolved == "မင်္ဂလာပါ"
    assert used_fallback is True
    assert fallback_source == "override"

from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
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

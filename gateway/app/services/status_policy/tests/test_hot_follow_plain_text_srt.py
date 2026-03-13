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

from gateway.app.routers import tasks as tasks_router


def test_plain_text_is_wrapped_to_single_srt():
    task = {"duration_sec": 12}
    source = "第一行中文\n第二行中文"
    text, mode = tasks_router._hf_normalize_subtitles_save_text(task, source)
    assert mode == "plain_text_wrapped"
    assert "-->" in text
    assert "第一行中文" in text
    assert "第二行中文" in text


def test_valid_srt_is_preserved():
    task = {"duration_sec": 12}
    source = "1\n00:00:00,000 --> 00:00:03,000\n缅文字幕\n"
    text, mode = tasks_router._hf_normalize_subtitles_save_text(task, source)
    assert mode == "srt"
    assert text.strip() == source.strip()


def test_target_lang_gate_blocks_non_myanmar_text_for_burmese_tts():
    result = tasks_router._hf_target_lang_gate(
        "1\n00:00:00,000 --> 00:00:03,000\nHello lipstick matte finish\n",
        target_lang="my",
    )
    assert result["allow"] is False
    assert result["reason"] == "target_lang_mismatch"

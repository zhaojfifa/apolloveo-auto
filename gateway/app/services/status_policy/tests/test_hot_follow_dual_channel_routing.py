import ast
from pathlib import Path


def _load_dual_channel_helper():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {
        "_hf_plain_text_signal",
        "_hf_load_normalized_source_text",
        "_hf_dual_channel_state",
    }
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {
        "Any": object,
        "parse_pipeline_config": lambda _v: {},
        "_hf_load_origin_subtitles_text": lambda _task: "",
        "_hf_load_subtitles_text": lambda *_args, **_kwargs: "",
        "task_base_dir": lambda _task_id: Path("."),
    }
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return namespace["_hf_dual_channel_state"], namespace


def test_hot_follow_dual_channel_detects_voice_led_when_transcript_exists():
    helper, ns = _load_dual_channel_helper()
    task = {"task_id": "hf-voice-led-01", "pipeline_config": ""}
    ns["_hf_load_origin_subtitles_text"] = lambda _task: "this is a normal spoken transcript"
    ns["_hf_load_normalized_source_text"] = lambda *_args, **_kwargs: "this is a normal spoken transcript"
    state = helper("hf-voice-led-01", task)
    assert state["speech_detected"] is True
    assert state["content_mode"] == "voice_led"


def test_hot_follow_dual_channel_detects_subtitle_led_candidate_from_subtitle_stream_hint():
    helper, ns = _load_dual_channel_helper()
    task = {"task_id": "hf-subtitle-led-01", "pipeline_config": ""}
    ns["parse_pipeline_config"] = lambda _v: {"subtitle_stream": "true"}
    state = helper("hf-subtitle-led-01", task)
    assert state["speech_detected"] is False
    assert state["onscreen_text_detected"] is True
    assert state["content_mode"] == "subtitle_led_candidate"


def test_hot_follow_dual_channel_detects_silent_candidate_when_no_signals():
    helper, _ns = _load_dual_channel_helper()
    task = {"task_id": "hf-silent-01", "pipeline_config": ""}
    state = helper("hf-silent-01", task)
    assert state["speech_detected"] is False
    assert state["onscreen_text_detected"] is False
    assert state["content_mode"] == "silent_candidate"

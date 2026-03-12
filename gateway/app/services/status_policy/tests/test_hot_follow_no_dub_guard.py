import ast
from pathlib import Path


def _load_no_dub_helper():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {
        "_hf_plain_text_signal",
        "_hf_has_usable_dub_text",
        "_hf_load_normalized_source_text",
        "_hf_dub_input_text",
        "_hf_detect_no_dub_candidate",
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
    return namespace["_hf_detect_no_dub_candidate"]


def test_hot_follow_no_dub_detects_empty_silent_candidate():
    detect = _load_no_dub_helper()
    task = {
        "task_id": "hf-no-dub-01",
        "kind": "hot_follow",
        "title": "无人声涂抹音",
        "pipeline_config": "",
    }

    state = detect("hf-no-dub-01", task)

    assert state["no_dub"] is True
    assert state["no_dub_reason"] == "no_speech_detected"


def test_hot_follow_no_dub_allows_manual_text_override():
    detect = _load_no_dub_helper()
    task = {
        "task_id": "hf-no-dub-02",
        "kind": "hot_follow",
        "title": "无人声涂抹音",
        "pipeline_config": "",
    }

    state = detect("hf-no-dub-02", task, manual_text="这是手工补充的配音文本")

    assert state["no_dub"] is False
    assert state["no_dub_reason"] is None

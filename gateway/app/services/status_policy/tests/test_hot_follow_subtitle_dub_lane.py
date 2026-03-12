import ast
from pathlib import Path


def _load_dub_input_helper():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {
        "_hf_load_normalized_source_text",
        "_hf_dub_input_text",
    }
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {
        "_hf_load_subtitles_text": lambda *_args, **_kwargs: "",
        "_hf_load_origin_subtitles_text": lambda _task: "",
        "task_base_dir": lambda _task_id: Path("."),
    }
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return namespace["_hf_dub_input_text"], namespace


def test_hot_follow_dub_input_prefers_manual_then_edited_then_normalized_then_origin():
    helper, ns = _load_dub_input_helper()
    task = {"task_id": "hf-dub-lane-01"}

    ns["_hf_load_subtitles_text"] = lambda *_args, **_kwargs: "edited text"
    ns["_hf_load_origin_subtitles_text"] = lambda _task: "origin text"
    ns["_hf_load_normalized_source_text"] = lambda *_args, **_kwargs: "normalized text"

    assert helper("hf-dub-lane-01", task, "manual text") == "manual text"
    assert helper("hf-dub-lane-01", task, None) == "edited text"

    ns["_hf_load_subtitles_text"] = lambda *_args, **_kwargs: ""
    assert helper("hf-dub-lane-01", task, None) == "normalized text"

    ns["_hf_load_normalized_source_text"] = lambda *_args, **_kwargs: ""
    assert helper("hf-dub-lane-01", task, None) == "origin text"

import ast
from pathlib import Path


def _load_helpers():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {"_count_srt_cues", "_build_translation_qa_summary", "_build_workbench_debug_payload"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {"re": __import__("re"), "Any": object}
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return (
        namespace["_count_srt_cues"],
        namespace["_build_translation_qa_summary"],
        namespace["_build_workbench_debug_payload"],
    )


def test_translation_qa_summary_counts_and_mismatch():
    _, build_translation_qa_summary, _ = _load_helpers()
    origin = "1\n00:00:00,000 --> 00:00:01,000\nA\n\n2\n00:00:01,000 --> 00:00:02,000\nB\n"
    edited = "1\n00:00:00,000 --> 00:00:01,000\nX\n"
    qa = build_translation_qa_summary(origin, edited)
    assert qa["source_count"] == 2
    assert qa["translated_count"] == 1
    assert qa["has_mismatch"] is True


def test_workbench_debug_payload_gate():
    _, _, build_workbench_debug_payload = _load_helpers()
    hidden = build_workbench_debug_payload(False, [{"k": "v"}], {"ffmpeg_cmd": "ffmpeg ..."})
    shown = build_workbench_debug_payload(True, [{"k": "v"}], {"ffmpeg_cmd": "ffmpeg ..."})
    assert hidden == {}
    assert shown["compose_last_ffmpeg_cmd"] == "ffmpeg ..."
    assert isinstance(shown["scene_outputs"], list)

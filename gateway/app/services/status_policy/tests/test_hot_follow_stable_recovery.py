import ast
from pathlib import Path


def _load_helpers():
    tasks_src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tasks_tree = ast.parse(tasks_src)
    task_keep = {"_hf_state_from_status", "_hf_pipeline_state"}
    task_selected = [node for node in tasks_tree.body if isinstance(node, ast.FunctionDef) and node.name in task_keep]
    task_module = ast.Module(body=task_selected, type_ignores=[])
    task_ns = {"Any": object}
    exec(compile(task_module, "gateway/app/routers/tasks.py", "exec"), task_ns)

    subtitles_src = Path("gateway/app/steps/subtitles.py").read_text(encoding="utf-8-sig")
    subtitles_tree = ast.parse(subtitles_src)
    subtitles_keep = {"_safe_non_negative_float", "_sanitize_segment_timing"}
    subtitles_selected = [node for node in subtitles_tree.body if isinstance(node, ast.FunctionDef) and node.name in subtitles_keep]
    subtitles_module = ast.Module(body=subtitles_selected, type_ignores=[])
    subtitles_ns = {"isfinite": __import__("math").isfinite}
    exec(compile(subtitles_module, "gateway/app/steps/subtitles.py", "exec"), subtitles_ns)

    return task_ns["_hf_pipeline_state"], subtitles_ns["_sanitize_segment_timing"]


def test_subtitle_segment_timing_sanitizes_none_values():
    _, sanitize_segment_timing = _load_helpers()
    segments = [
        {"index": 1, "start": None, "end": 1.25, "origin": "a"},
        {"index": 2, "start": 2.0, "end": None, "origin": "b"},
        {"index": 3, "start": None, "end": None, "origin": "c"},
    ]

    sanitized = sanitize_segment_timing(segments)

    assert sanitized[0]["start"] == 0.0
    assert sanitized[0]["end"] == 1.25
    assert sanitized[1]["start"] == 2.0
    assert sanitized[1]["end"] == 2.0
    assert sanitized[2]["start"] == 0.0
    assert sanitized[2]["end"] == 0.0


def test_hot_follow_pipeline_state_prefers_error_over_artifact_done():
    hf_pipeline_state, _ = _load_helpers()
    parse_status, _ = hf_pipeline_state(
        {"parse_status": "ready", "parse_error": "internal error", "raw_path": "deliver/tasks/x/raw.mp4"},
        "parse",
    )
    subtitles_status, _ = hf_pipeline_state(
        {
            "subtitles_status": "ready",
            "subtitles_error": "unsupported operand type(s) for +: 'float' and 'NoneType'",
            "origin_srt_path": "deliver/subtitles/x/origin.srt",
            "mm_srt_path": "deliver/subtitles/x/mm.srt",
        },
        "subtitles",
    )

    assert parse_status == "failed"
    assert subtitles_status == "failed"

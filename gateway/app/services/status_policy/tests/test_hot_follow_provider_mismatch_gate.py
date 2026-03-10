import ast
from pathlib import Path


def _load_compute_hot_follow_state():
    src = Path("gateway/app/services/status_policy/hot_follow_state.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {"_as_dict", "_as_list", "_pick_final", "_resolve_final_url", "compute_hot_follow_state"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {"Any": object, "Dict": dict}
    exec(compile(module, "gateway/app/services/status_policy/hot_follow_state.py", "exec"), namespace)
    return namespace["compute_hot_follow_state"]


def test_hot_follow_provider_mismatch_blocks_compose_ready_even_if_final_exists():
    compute_hot_follow_state = _load_compute_hot_follow_state()
    task = {
        "task_id": "t1",
        "kind": "hot_follow",
        "compose_status": "done",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/t1/audio_mm.mp3",
    }
    base_state = {
        "task_id": "t1",
        "final": {"exists": True, "url": "/v1/tasks/t1/final"},
        "audio": {
            "status": "done",
            "tts_voice": "my-MM-NilarNeural",
            "voiceover_url": "/v1/tasks/t1/audio_mm",
            "audio_ready": False,
        },
        "compose": {"last": {"status": "done"}},
        "pipeline": [{"key": "compose", "status": "done", "state": "done"}],
        "deliverables": [{"kind": "final", "status": "done", "state": "done", "url": "/v1/tasks/t1/final"}],
    }

    state = compute_hot_follow_state(task, base_state)

    assert state["ready_gate"]["audio_ready"] is False
    assert state["ready_gate"]["compose_ready"] is False
    assert state["ready_gate"]["publish_ready"] is False
    assert state["compose"]["last"]["status"] == "pending"
    assert state["pipeline"][0]["status"] == "pending"
    assert state["deliverables"][0]["status"] == "pending"

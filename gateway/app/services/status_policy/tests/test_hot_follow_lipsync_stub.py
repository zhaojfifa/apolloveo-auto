import ast
import os
from pathlib import Path


def _load_lipsync_stub():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_hot_follow_lipsync_stub"
    ]
    module = ast.Module(body=selected, type_ignores=[])

    class _HTTPException(Exception):
        def __init__(self, status_code=None, detail=None):
            self.status_code = status_code
            self.detail = detail

    class _Logger:
        def warning(self, *_args, **_kwargs):
            return None

    namespace = {
        "Any": object,
        "os": os,
        "HTTPException": _HTTPException,
        "logger": _Logger(),
    }
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return namespace["_run_hot_follow_lipsync_stub"]


def test_hot_follow_lipsync_stub_off_returns_basic_source():
    helper = _load_lipsync_stub()
    state = helper("hf-lipsync-01", False)
    assert state["enabled"] is False
    assert state["status"] == "off"
    assert state["compose_video_source"] == "basic"


def test_hot_follow_lipsync_stub_soft_fail_returns_fallback_basic(monkeypatch):
    helper = _load_lipsync_stub()
    monkeypatch.setenv("HF_LIPSYNC_SOFT_FAIL", "1")
    state = helper("hf-lipsync-02", True)
    assert state["enabled"] is True
    assert state["status"] == "fallback_basic"
    assert state["compose_video_source"] == "basic"
    assert "continuing basic compose" in state["warning"]

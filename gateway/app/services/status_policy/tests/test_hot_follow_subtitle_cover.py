import ast
import os
from pathlib import Path


def _load_cover_helper():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_hf_source_subtitle_cover_filter"
    ]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {"Any": object, "os": os}
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return namespace["_hf_source_subtitle_cover_filter"]


def test_hot_follow_subtitle_cover_filter_disabled_by_default():
    helper = _load_cover_helper()
    assert helper({}, {}) is None


def test_hot_follow_subtitle_cover_filter_returns_bottom_band_drawbox_when_enabled():
    helper = _load_cover_helper()
    expr = helper(
        {"source_subtitle_cover_enabled": True, "source_subtitle_cover_mode": "bottom_band"},
        {},
    )
    assert expr is not None
    assert "drawbox=" in expr
    assert "y=ih*0.78" in expr
    assert "h=ih*0.22" in expr

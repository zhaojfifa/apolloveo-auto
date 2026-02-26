from pathlib import Path


def test_workbench_ui_has_compose_done_guard_sources():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "function isComposeDone(hub)" in js
    assert "final.exists" in js
    assert "data.final_key" in js
    assert "composeLast.status" in js
    assert "it.key === \"compose\"" in js


def test_workbench_ui_done_uses_ready_text_not_not_ready():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "const done = isComposeDone(currentHub);" in js
    assert "done ? t(\"hot_follow_compose_reason_ready\", \"已完成\")" in js


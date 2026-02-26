from pathlib import Path


def test_workbench_ui_has_compose_done_guard_sources():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "function isComposeDone(hub)" in js
    assert "final.exists" in js
    assert "data.final_key" in js
    assert "task.final_key" in js
    assert "composeLast.status" in js
    assert "it.key === \"compose\"" in js


def test_workbench_ui_done_forces_ready_text_and_hides_readiness():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "const done = isComposeDone(currentHub);" in js
    assert "已就绪（已完成）" in js
    assert "composeReadinessSectionEl.classList.toggle(\"hidden\", done)" in js
    assert "done ? \"重新合成\"" in js


def test_workbench_hub_poll_uses_no_store_with_timestamp_bust():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "t=${Date.now()}" in js
    assert "cache: \"no-store\"" in js


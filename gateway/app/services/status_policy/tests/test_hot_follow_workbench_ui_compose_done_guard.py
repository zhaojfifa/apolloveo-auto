from pathlib import Path


def test_compose_done_sources_are_present():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "function isComposeDone(hub)" in js
    assert "((data.final || {}).exists === true)" in js
    assert "data.final_key || data.final_url" in js
    assert "task.final_key || task.final_url" in js
    assert "isDoneStatus(composeLast.status)" in js
    assert "it.key === \"compose\" && isDoneStatus(it.status)" in js


def test_done_branch_does_not_render_not_ready_text():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "done ? t(\"hot_follow_compose_reason_ready\", \"已就绪（已完成）\")" in js
    assert "composeReadinessSectionEl.classList.toggle(\"hidden\", done)" in js
    assert "done ? \"重新合成\"" in js


from pathlib import Path


def test_compose_done_sources_are_present():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "function isComposeDone(hub)" in js
    assert "((data.final || {}).exists === true)" in js
    assert "data.final_key || data.final_url" in js
    assert "task.final_key || task.final_url" in js
    assert "isDoneStatus(composeLast.status)" in js
    assert "it.key === \"compose\" && isDoneStatus(it.status)" in js


def test_done_branch_hides_readiness_and_sets_recompose_label():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "const done = isComposeDone(currentHub);" in js
    assert "composeReadinessSectionEl.classList.toggle(\"hidden\", done)" in js
    assert "done ? \"重新合成\"" in js
    assert "done ? t(\"hot_follow_compose_reason_ready\"" in js


def test_poll_uses_no_store_with_timestamp_bust():
    js = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8")
    assert "t=${Date.now()}" in js
    assert "cache: \"no-store\"" in js


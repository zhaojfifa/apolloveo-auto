from pathlib import Path


def test_hot_follow_workbench_template_keeps_srt_first_semantics():
    template = Path("gateway/app/templates/hot_follow_workbench.html").read_text(encoding="utf-8")
    script = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8-sig")

    assert "当前目标语言 SRT 预览（主对象）" in template
    assert "当前目标语言字幕编辑区（SRT 主对象）" in template
    assert "辅助输入（原文 / 候选，helper only）" in template
    assert "primary_editable_text" in script
    assert "primary_editable_format" in script


def test_hot_follow_workbench_template_renders_advisory_as_secondary_guidance():
    template = Path("gateway/app/templates/hot_follow_workbench.html").read_text(encoding="utf-8")
    script = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8-sig")

    assert 'id="hf_advisory_card"' in template
    assert "附加建议（只读）" in template
    assert 'id="hf_advisory_level"' in template
    assert 'id="hf_advisory_action"' in template
    assert 'id="hf_advisory_hint"' in template
    assert 'id="hf_advisory_explanation"' in template
    assert 'id="hf_advisory_evidence"' in template
    assert 'const advisoryCardEl = document.getElementById("hf_advisory_card");' in script
    assert "function renderAdvisory()" in script
    assert 'const advisory = (currentHub && currentHub.advisory) || null;' in script
    assert 'advisoryCardEl.classList.toggle("hidden", !hasAdvisory);' in script

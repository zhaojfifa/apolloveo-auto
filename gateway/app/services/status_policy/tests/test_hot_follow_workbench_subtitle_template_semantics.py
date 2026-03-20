from pathlib import Path


def test_hot_follow_workbench_template_keeps_srt_first_semantics():
    template = Path("gateway/app/templates/hot_follow_workbench.html").read_text(encoding="utf-8")
    script = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8-sig")

    assert "当前目标语言 SRT 预览（主对象）" in template
    assert "当前目标语言字幕编辑区（SRT 主对象）" in template
    assert "辅助输入（原文 / 候选，helper only）" in template
    assert "primary_editable_text" in script
    assert "primary_editable_format" in script
    assert "mergeTranslatedSrtIntoPrimary" in script
    assert "parseSrtSegments" in script


def test_hot_follow_workbench_template_keeps_source_link_and_recompose_controls():
    template = Path("gateway/app/templates/hot_follow_workbench.html").read_text(encoding="utf-8")
    script = Path("gateway/app/static/js/hot_follow_workbench.js").read_text(encoding="utf-8-sig")

    assert 'id="hf_source_url_text"' in template
    assert 'id="hf_source_url_open"' in template
    assert 'id="hf_source_url_copy"' in template
    assert "renderSourceLinkCard" in script
    assert "copyTextToClipboard" in script
    assert "requires_recompose" in script
    assert "重新合成最终视频" in script

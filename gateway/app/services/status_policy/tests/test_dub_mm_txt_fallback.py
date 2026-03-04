import ast
from pathlib import Path


def _load_helpers():
    src = Path("gateway/app/services/steps_v1.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {"_SRT_TIME_RE", "_srt_to_txt", "_pick_mm_text_fallback", "_resolve_mm_txt_text"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    selected += [node for node in tree.body if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_SRT_TIME_RE" for t in node.targets)]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {"re": __import__("re")}
    exec(compile(module, "gateway/app/services/steps_v1.py", "exec"), namespace)
    return (
        namespace["_pick_mm_text_fallback"],
        namespace["_resolve_mm_txt_text"],
    )


def test_mm_txt_fallback_uses_mm_srt_when_mm_txt_missing():
    _, resolve_mm_txt_text = _load_helpers()
    srt_text = """1
00:00:00,000 --> 00:00:01,000
မင်္ဂလာပါ
"""
    text, used_fallback, source = resolve_mm_txt_text(
        mm_txt_text="",
        override_text=None,
        edited_text=None,
        mm_srt_text=srt_text,
    )
    assert used_fallback is True
    assert source == "mm_srt"
    assert "မင်္ဂလာပါ" in text


def test_mm_txt_fallback_not_triggered_when_mm_txt_exists():
    _, resolve_mm_txt_text = _load_helpers()
    text, used_fallback, source = resolve_mm_txt_text(
        mm_txt_text="already prepared text",
        override_text=None,
        edited_text="edited text",
        mm_srt_text="1\n00:00:00,000 --> 00:00:01,000\nfrom srt\n",
    )
    assert used_fallback is False
    assert source == "mm_txt"
    assert text == "already prepared text"

import re
from pathlib import Path


def _extract_brace_object(src: str, start: int) -> str:
    i = src.find("{", start)
    assert i >= 0, "object start not found"
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1 : j]
    raise AssertionError("object block not closed")


def _extract_sop_keys() -> set[str]:
    files = [
        Path("gateway/app/static/js/hot_follow_new.js"),
        Path("gateway/app/static/js/hot_follow_workbench.js"),
        Path("gateway/app/static/js/hot_follow_delivery.js"),
        Path("gateway/app/templates/hot_follow_new.html"),
        Path("gateway/app/templates/hot_follow_workbench.html"),
        Path("gateway/app/templates/hot_follow_publish.html"),
    ]
    keys: set[str] = set()
    for path in files:
        src = path.read_text(encoding="utf-8", errors="ignore")
        keys.update(re.findall(r'data-i18n="([^"]+)"', src))
        keys.update(re.findall(r'data-i18n-placeholder="([^"]+)"', src))
        keys.update(re.findall(r'data-i18n-title="([^"]+)"', src))
        keys.update(re.findall(r'\bt\(\s*"([^"]+)"', src))
    return {k for k in keys if k.startswith("hot_follow_")}


def _extract_locale_keys(locale: str) -> set[str]:
    src = Path("gateway/app/static/js/i18n_v185.js").read_text(encoding="utf-8", errors="ignore")
    m = re.search(rf"\b{locale}\s*:\s*\{{", src)
    assert m, f"locale block not found: {locale}"
    block = _extract_brace_object(src, m.start())
    quoted = set(re.findall(r'"([^"]+)"\s*:', block))
    bare = set(re.findall(r"\b([A-Za-z0-9_.]+)\s*:", block))
    merged: set[str] = set()
    for assign in re.finditer(rf"Object\.assign\(\s*CLIENT_DICT\.{locale}\s*,\s*\{{", src):
        payload = _extract_brace_object(src, assign.start())
        merged.update(re.findall(r'"([^"]+)"\s*:', payload))
        merged.update(re.findall(r"\b([A-Za-z0-9_.]+)\s*:", payload))
    return quoted | bare | merged


def test_sop_i18n_keys_exist_for_zh_mm():
    sop_keys = _extract_sop_keys()
    assert sop_keys, "no SOP i18n keys found"
    zh_keys = _extract_locale_keys("zh")
    mm_keys = _extract_locale_keys("mm")
    missing_zh = sorted(k for k in sop_keys if k not in zh_keys)
    missing_mm = sorted(k for k in sop_keys if k not in mm_keys)
    assert not missing_zh, f"missing zh SOP keys: {missing_zh}"
    assert not missing_mm, f"missing mm SOP keys: {missing_mm}"

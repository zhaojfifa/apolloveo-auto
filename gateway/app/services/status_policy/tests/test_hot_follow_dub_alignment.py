import ast
from pathlib import Path


def _load_helpers():
    src = Path("gateway/app/services/steps_v1.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {"_build_atempo_chain"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {}
    exec(compile(module, "gateway/app/services/steps_v1.py", "exec"), namespace)
    return namespace["_build_atempo_chain"]


def test_build_atempo_chain_uses_speedup_direction_for_over_budget_audio():
    build_atempo_chain = _load_helpers()
    chain = build_atempo_chain(1.15)
    assert chain == "atempo=1.150000"


def test_build_atempo_chain_splits_speeds_over_two_x():
    build_atempo_chain = _load_helpers()
    chain = build_atempo_chain(3.0)
    assert chain == "atempo=2.0,atempo=1.500000"

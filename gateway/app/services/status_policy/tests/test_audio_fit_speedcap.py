import ast
from pathlib import Path


def _load_helpers():
    src = Path("gateway/app/routers/tasks.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    keep = {"_build_atempo_chain", "_resolve_audio_fit_max_speed", "_compute_audio_fit_speeds"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in keep]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {}
    exec(compile(module, "gateway/app/routers/tasks.py", "exec"), namespace)
    return (
        namespace["_build_atempo_chain"],
        namespace["_resolve_audio_fit_max_speed"],
        namespace["_compute_audio_fit_speeds"],
    )


def test_audio_fit_speedcap_default():
    _, _resolve_audio_fit_max_speed, _compute_audio_fit_speeds = _load_helpers()
    max_speed, source = _resolve_audio_fit_max_speed({})
    assert max_speed == 1.25
    assert source == "default"

    need_speed, applied_speed = _compute_audio_fit_speeds(10.0, 20.0, max_speed)
    assert round(need_speed, 3) == 2.0
    assert round(applied_speed, 3) == 1.25


def test_audio_fit_speedcap_operator_2x():
    _, _resolve_audio_fit_max_speed, _compute_audio_fit_speeds = _load_helpers()
    max_speed, source = _resolve_audio_fit_max_speed({"audio_fit_max_speed": 2.0})
    assert max_speed == 2.0
    assert source == "operator"

    need_speed, applied_speed = _compute_audio_fit_speeds(10.0, 20.0, max_speed)
    assert round(need_speed, 3) == 2.0
    assert round(applied_speed, 3) == 2.0


def test_audio_fit_speedcap_clamp():
    _, _resolve_audio_fit_max_speed, _ = _load_helpers()
    high, high_source = _resolve_audio_fit_max_speed({"audio_fit_max_speed": 5.0})
    low, low_source = _resolve_audio_fit_max_speed({"audio_fit_max_speed": 0.5})

    assert high == 2.0
    assert low == 1.0
    assert high_source == "operator"
    assert low_source == "operator"


def test_atempo_chain_chains_over_2x():
    _build_atempo_chain, _, _ = _load_helpers()
    chain = _build_atempo_chain(3.0)
    assert chain == "atempo=2.0,atempo=1.500000"

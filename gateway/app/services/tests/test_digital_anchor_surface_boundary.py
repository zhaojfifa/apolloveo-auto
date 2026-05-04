"""Surface-boundary tests for Digital Anchor PR-4 surfaces."""
from __future__ import annotations

from pathlib import Path

import pytest

from gateway.app.services.digital_anchor import closure_binding


def _try_import_router():
    try:
        from gateway.app.routers import digital_anchor_closure  # type: ignore
        return digital_anchor_closure
    except Exception:
        return None


def _router_source() -> str:
    return (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "routers"
        / "digital_anchor_closure.py"
    ).read_text()


def _tasks_router_source() -> str:
    return (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "routers"
        / "tasks.py"
    ).read_text()


def test_router_prefix_is_digital_anchor_scoped():
    module = _try_import_router()
    if module is not None:
        routes = [r.path for r in module.api_router.routes]
        assert routes
        for path in routes:
            assert path.startswith("/api/digital-anchor/closures"), path
    else:
        assert 'prefix="/api/digital-anchor/closures"' in _router_source()


def test_router_has_no_packet_or_admin_paths():
    module = _try_import_router()
    forbidden = ("/packet", "/admin", "/tasks/connect", "/provider", "/vendor")
    if module is not None:
        for r in module.api_router.routes:
            for sub in forbidden:
                assert sub not in r.path
    else:
        source = _router_source()
        for line in source.splitlines():
            if "@api_router" in line:
                for sub in forbidden:
                    assert sub not in line


def test_temp_digital_anchor_placeholder_removed():
    """The new-task route contract §3 mandates removal of the temp path entry."""
    source = _tasks_router_source()
    # The TEMP dict was emptied; digital_anchor must NOT remain inside it.
    # Find the dict literal and verify "digital_anchor" is not inside its
    # immediate scope (it is allowed elsewhere — function names, comments).
    start = source.find("_TEMP_CONNECTED_LINES")
    assert start != -1
    # Scan from start until the closing brace of the dict literal.
    brace_open = source.find("{", start)
    depth = 1
    idx = brace_open + 1
    while idx < len(source) and depth > 0:
        if source[idx] == "{":
            depth += 1
        elif source[idx] == "}":
            depth -= 1
        idx += 1
    snippet = source[brace_open:idx]
    assert '"digital_anchor"' not in snippet, (
        "digital_anchor MUST be removed from _TEMP_CONNECTED_LINES per "
        "new_task_route_contract_v1.md §3"
    )


def test_formal_route_registered_in_tasks_router():
    source = _tasks_router_source()
    assert "DIGITAL_ANCHOR_CREATE_ROUTE" in source
    assert "tasks_digital_anchor_new" in source
    assert "create_digital_anchor_task" in source


def test_template_block_is_gated_to_digital_anchor():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "task_publish_hub.html"
    ).read_text()
    closure_token = 'id="digital-anchor-closure-block"'
    gate_token = '_da_kind == "digital_anchor"'
    assert closure_token in template
    gate_pos = template.index(gate_token)
    closure_pos = template.index(closure_token)
    assert gate_pos < closure_pos


def test_template_does_not_expose_provider_or_vendor_controls():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "task_publish_hub.html"
    ).read_text()
    closure_idx = template.index('id="digital-anchor-closure-block"')
    closure_segment = template[closure_idx : closure_idx + 6000].lower()
    for forbidden in (
        'name="vendor_id"',
        'name="model_id"',
        'name="provider_id"',
        'name="engine_id"',
        'name="avatar_engine"',
        'name="tts_provider"',
        'name="lip_sync_engine"',
    ):
        assert forbidden not in closure_segment


def test_new_task_template_does_not_expose_provider_controls():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "digital_anchor_new.html"
    ).read_text().lower()
    for forbidden in (
        'name="vendor_id"',
        'name="model_id"',
        'name="provider_id"',
        'name="engine_id"',
        'name="avatar_engine"',
        'name="tts_provider"',
        'name="lip_sync_engine"',
    ):
        assert forbidden not in template


def test_new_tasks_card_points_to_formal_route():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "tasks_newtasks.html"
    ).read_text()
    assert "/tasks/digital-anchor/new" in template
    assert "/tasks/connect/digital_anchor/new" not in template


def test_closure_binding_module_rejects_other_lines():
    closure_binding.reset_for_tests()
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.get_or_create_for_task(
            {"task_id": "x", "kind": "matrix_script", "packet": {}}
        )

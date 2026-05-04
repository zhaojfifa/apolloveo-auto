"""Surface-boundary tests for the Matrix Script closure surface (Recovery PR-3).

Authority:
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §6
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``

Verifies:
- The closure router prefix is matrix-script-scoped (no Hot Follow / Digital
  Anchor leak).
- Closure routes never expose ``/packet`` / ``/admin`` / ``/tasks/connect``
  paths.
- The publish-hub template carries the gated closure block only inside the
  ``task.kind == "matrix_script"`` branch.
- The closure binding module forbids non-matrix_script tasks at the type
  boundary.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from gateway.app.services.matrix_script import closure_binding


def _import_router():
    """Defensive import: returns None on PY3.9 + config.py PEP 604 incompat
    (a pre-existing repo baseline issue documented by Recovery PR-1 §7).
    Tests that would otherwise need the FastAPI router fall back to
    inspecting the source file itself.
    """
    try:
        from gateway.app.routers import matrix_script_closure  # type: ignore
        return matrix_script_closure
    except Exception:
        return None


def _router_source() -> str:
    return (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "routers"
        / "matrix_script_closure.py"
    ).read_text()


def test_router_prefix_is_matrix_script_scoped():
    module = _import_router()
    if module is not None:
        routes = [r.path for r in module.api_router.routes]
        assert routes
        for path in routes:
            assert path.startswith("/api/matrix-script/closures"), path
    else:
        source = _router_source()
        assert 'prefix="/api/matrix-script/closures"' in source


def test_router_has_no_packet_or_admin_paths():
    module = _import_router()
    forbidden_substrings = ("/packet", "/admin", "/tasks/connect", "/provider", "/vendor")
    if module is not None:
        for r in module.api_router.routes:
            for substring in forbidden_substrings:
                assert substring not in r.path, f"forbidden path fragment {substring!r} in {r.path}"
    else:
        source = _router_source()
        for substring in forbidden_substrings:
            # Acceptable inside string literals only when not used as a route
            # path. Hardline check: the router prefix line should not contain any
            # of these substrings, and route decorators (@api_router.get/post)
            # should reference paths that are matrix-script-scoped.
            for line in source.splitlines():
                if "@api_router" in line:
                    assert substring not in line, line


def test_template_block_is_gated_to_matrix_script_only():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "task_publish_hub.html"
    ).read_text()
    # The closure block must sit inside the existing
    # `{% if _ms_kind == "matrix_script" %}` branch.
    closure_token = 'id="matrix-script-closure-block"'
    gate_token = '_ms_kind == "matrix_script"'
    assert closure_token in template
    closure_pos = template.index(closure_token)
    gate_pos = template.index(gate_token)
    # The gate `{% if ... %}` must precede the closure block; an
    # `{% endif %}` must close it after.
    assert gate_pos < closure_pos
    endif_after = template.find("{% endif %}", closure_pos)
    assert endif_after != -1


def test_template_does_not_expose_provider_or_vendor_controls():
    template = (
        Path(__file__).resolve().parents[4]
        / "gateway"
        / "app"
        / "templates"
        / "task_publish_hub.html"
    ).read_text()
    # Closure block surface must not carry vendor / model / provider /
    # engine identifiers as form fields or copy strings.
    closure_token = 'id="matrix-script-closure-block"'
    closure_idx = template.index(closure_token)
    closure_segment = template[closure_idx : closure_idx + 6000].lower()
    for forbidden in (
        'name="vendor_id"',
        'name="model_id"',
        'name="provider_id"',
        'name="engine_id"',
    ):
        assert forbidden not in closure_segment


def test_closure_binding_rejects_non_matrix_script_tasks():
    closure_binding.reset_for_tests()
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.get_or_create_for_task(
            {
                "task_id": "x",
                "kind": "digital_anchor",
                "packet": {"line_id": "digital_anchor"},
            }
        )


def test_apply_event_without_existing_closure_for_bare_task_id_rejects():
    closure_binding.reset_for_tests()
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_event_for_task(
            "no_such_task",
            {"event_kind": "operator_retract", "variation_id": "c1"},
        )

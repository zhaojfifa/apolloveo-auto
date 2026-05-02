"""Workbench panel-dispatch confirmation for Matrix Script (§8.B).

Authority:
- ``docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md`` §8.B
- ``docs/contracts/workbench_panel_dispatch_contract_v1.md``
- ``docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md``
- ``docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md`` (§8.A)

These tests use a **fresh, contract-clean** Matrix Script sample created via
the formal POST ``/tasks/matrix-script/new`` endpoint (the §8.A guard is
active, so the ``source_script_ref`` value is an opaque reference, not body
text). The old invalid sample is NOT used as evidence.

What is proved end-to-end:

1. Which route is hit when an operator opens the new task. The redirect
   target of POST is ``/tasks/{task_id}?created=matrix_script``; GET on
   that path returns 200 against the same in-memory repo.
2. Which panel kind the resolver mounts. ``PANEL_REF_DISPATCH`` maps the
   two seeded ``line_specific_refs[]`` entries
   (``matrix_script_variation_matrix``, ``matrix_script_slot_pack``) to
   ``panel_kind="matrix_script"``.
3. Whether the rendered ``/tasks/{task_id}`` HTML actually mounts the
   Matrix Script Phase B variation surface — we assert the
   ``data-role="matrix-script-variation-panel"`` block exists, the
   contract projection name ``matrix_script_workbench_variation_surface_v1``
   is referenced, and the line-panel slot is data-tagged
   ``data-panel-kind="matrix_script"``.
4. Whether the rendered result is the generic engineering shell or the
   correct Matrix Script surface. The template that renders this URL is
   the shared ``task_workbench.html`` (per ``WorkbenchSpec`` registry
   fallback), but it gates the Matrix Script Variation Panel block on
   ``ops_workbench_panel.panel_kind == "matrix_script"``. Confirming that
   the gate fires for a contract-clean sample distinguishes "panel did
   not mount" (broken dispatch) from "panel mounted but appeared empty"
   (the §8.C concern, out of scope here).
"""
from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router


CONTRACT_CLEAN_REF = "content://matrix-script/source/8b-fresh-001"
TOPIC = "§8.B fresh contract-clean Matrix Script sample"


class _InMemoryRepo:
    """Minimal repo that round-trips the formal create payload.

    The Matrix Script create handler stores the dict produced by
    ``build_matrix_script_task_payload``; subsequent GETs must read back
    ``packet`` and ``line_specific_refs`` so the workbench resolver can
    dispatch to ``panel_kind="matrix_script"``.
    """

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload)
        self._rows[str(row["task_id"])] = row
        return row

    def get(self, task_id: str) -> dict[str, Any] | None:
        row = self._rows.get(str(task_id))
        return dict(row) if row is not None else None


def _post_fresh_sample(client: TestClient) -> tuple[str, dict[str, str]]:
    """POST a fresh contract-clean sample. Returns (task_id, redirect_query)."""

    response = client.post(
        "/tasks/matrix-script/new",
        data={
            "topic": TOPIC,
            "source_script_ref": CONTRACT_CLEAN_REF,
            "source_language": "zh",
            "target_language": "mm",
            "target_platform": "TikTok",
            "variation_target_count": "4",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    location = response.headers["location"]
    assert location.startswith("/tasks/")
    task_id = location.split("/tasks/", 1)[1].split("?", 1)[0]
    return task_id, {"created": "matrix_script"}


def test_post_redirect_target_is_workbench_route(monkeypatch):
    """The POST redirect lands at the workbench route, not the generic
    `/tasks/connect/matrix_script/new` placeholder. Confirms which route
    operators are sent to immediately after a contract-clean create.
    """

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id, _ = _post_fresh_sample(client)
    finally:
        app.dependency_overrides.clear()

    assert task_id, "POST did not return a task_id"
    stored = repo.get(task_id)
    assert stored is not None
    assert stored["kind"] == "matrix_script"
    # The contract-clean sample carries the opaque ref end-to-end, NOT body
    # text. This proves §8.A's guard is in force at the moment of dispatch.
    assert stored["source_url"] == CONTRACT_CLEAN_REF
    assert stored["config"]["entry"]["source_script_ref"] == CONTRACT_CLEAN_REF


def test_fresh_sample_packet_seeds_dispatch_inputs(monkeypatch):
    """The persisted task carries the two `line_specific_refs[]` entries
    that ``PANEL_REF_DISPATCH`` keys to ``panel_kind="matrix_script"``.

    This is the *input* side of the resolver — without these, no
    contract-clean sample can ever reach the Phase B panel.
    """

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id, _ = _post_fresh_sample(client)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    assert stored is not None
    top_level_refs = {ref["ref_id"] for ref in stored["line_specific_refs"]}
    packet_refs = {ref["ref_id"] for ref in stored["packet"]["line_specific_refs"]}
    assert top_level_refs == {
        "matrix_script_variation_matrix",
        "matrix_script_slot_pack",
    }
    assert packet_refs == top_level_refs


def test_resolver_dispatches_fresh_sample_to_matrix_script_panel_kind(monkeypatch):
    """`resolve_line_specific_panel(packet)` is the dispatch boundary
    declared by `workbench_panel_dispatch_contract_v1`. For the fresh
    contract-clean sample it MUST return `panel_kind="matrix_script"`
    and surface both seeded ref_ids.
    """

    from gateway.app.services.operator_visible_surfaces.projections import (
        PANEL_REF_DISPATCH,
        resolve_line_specific_panel,
    )

    # Re-state the contract pin so the test fails loudly if the dispatch
    # contract drifts away from the resolver implementation.
    assert PANEL_REF_DISPATCH["matrix_script_variation_matrix"] == "matrix_script"
    assert PANEL_REF_DISPATCH["matrix_script_slot_pack"] == "matrix_script"

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id, _ = _post_fresh_sample(client)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    panel = resolve_line_specific_panel(stored["packet"])
    assert panel["panel_kind"] == "matrix_script"
    surfaced = {ref["ref_id"] for ref in panel["refs"]}
    assert surfaced == {
        "matrix_script_variation_matrix",
        "matrix_script_slot_pack",
    }


def test_get_workbench_renders_matrix_script_phase_b_variation_panel(monkeypatch):
    """End-to-end §8.B confirmation. POST a fresh contract-clean sample,
    GET ``/tasks/{task_id}``, and assert the rendered HTML mounts the
    Matrix Script Phase B variation panel.

    This is the load-bearing assertion: it proves the operator-visible
    workbench actually reaches the Matrix Script surface, not the generic
    shell, when the sample is contract-clean.
    """

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    captured: dict[str, Any] = {}

    real_render = tasks_router.render_template

    def capturing_render(*, request, name, ctx=None, status_code=200, headers=None):
        captured["template"] = name
        captured["panel_kind"] = (
            ((ctx or {}).get("task_json", {}) or {})
            .get("operator_surfaces", {})
            .get("workbench", {})
            .get("line_specific_panel", {})
            .get("panel_kind")
        )
        captured["matrix_script_surface_attached"] = (
            "matrix_script_variation_surface"
            in (
                ((ctx or {}).get("task_json", {}) or {}).get(
                    "operator_surfaces", {}
                ).get("workbench", {})
            )
        )
        return real_render(
            request=request,
            name=name,
            ctx=ctx,
            status_code=status_code,
            headers=headers,
        )

    monkeypatch.setattr(tasks_router, "render_template", capturing_render)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id, query = _post_fresh_sample(client)
        response = client.get(f"/tasks/{task_id}", params=query)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text

    # Workbench template choice — the registry fallback renders the shared
    # task_workbench.html shell. The contract does NOT require a per-line
    # template; it requires the resolver to mount panel_kind="matrix_script"
    # and the shell to gate the Matrix Script Phase B section on it.
    assert captured["template"] == "task_workbench.html"

    # Resolver dispatch — confirms PANEL_REF_DISPATCH fired.
    assert captured["panel_kind"] == "matrix_script"

    # Variation surface attached — confirms wiring.py attached the
    # `matrix_script_workbench_variation_surface_v1` projection to the
    # workbench bundle.
    assert captured["matrix_script_surface_attached"] is True

    # Rendered HTML contains the Matrix Script Phase B variation panel.
    body = response.text
    assert 'data-role="matrix-script-variation-panel"' in body, (
        "Matrix Script Phase B variation panel did not render — operator "
        "would land on the generic engineering shell instead of the line "
        "panel"
    )
    assert 'data-panel-kind="matrix_script"' in body
    assert "matrix_script_workbench_variation_surface_v1" in body
    # Each seeded ref_id must surface in the line-specific panel slot so
    # operators can confirm the dispatch happened.
    assert "matrix_script_variation_matrix" in body
    assert "matrix_script_slot_pack" in body
    # And the panel must NOT be the empty-slot fallback message.
    assert "No line_specific_refs[] on this packet" not in body

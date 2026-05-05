"""Phase B authoring end-to-end confirmation for Matrix Script (§8.C).

Authority:
- ``docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md`` §8.C
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Phase B deterministic authoring (addendum, 2026-05-03)"
- ``docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md``
- ``docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md`` (§8.A)
- ``docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md`` (§8.B)

These tests use a **fresh, contract-clean** Matrix Script sample created
via the formal POST ``/tasks/matrix-script/new`` endpoint. The §8.A guard
is active and §8.B confirmed dispatch; §8.C now proves that the
correctly-mounted Matrix Script Phase B variation panel receives real
resolvable axes / cells / slots truth, not the empty-fallback rendering
that blocked Plan A trial evidence on the previous sample.

What is proved end-to-end:

1. The persisted task carries populated ``delta`` payloads on both LS1
   (``matrix_script_variation_matrix``) and LS2 (``matrix_script_slot_pack``)
   ref entries — both on the top-level mirror and the packet envelope
   mirror.
2. The Phase B projector consumes the authored deltas verbatim and
   emits non-empty ``variation_plan.axes`` / ``variation_plan.cells`` /
   ``copy_bundle.slots``.
3. The rendered ``/tasks/{task_id}`` HTML actually contains the canonical
   axis ids, the value tokens, and the cell / slot ids that the planner
   emits — and the empty-fallback messages are absent.
4. The cardinality of cells matches ``variation_target_count``.
5. The slot ``language_scope.target_language`` carries the entry's
   submitted target language.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router
from gateway.app.services.matrix_script.phase_b_authoring import (
    AUDIENCES,
    LENGTH_PICKS,
    LENGTH_RANGE,
    TONES,
)


CONTRACT_CLEAN_REF = "content://matrix-script/source/8c-fresh-001"
TOPIC = "§8.C fresh contract-clean Matrix Script sample"


class _InMemoryRepo:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload)
        self._rows[str(row["task_id"])] = row
        return row

    def get(self, task_id: str) -> dict[str, Any] | None:
        row = self._rows.get(str(task_id))
        return dict(row) if row is not None else None


def _post_fresh_sample(
    client: TestClient,
    *,
    variation_target_count: int = 4,
    target_language: str = "mm",
) -> str:
    response = client.post(
        "/tasks/matrix-script/new",
        data={
            "topic": TOPIC,
            "source_script_ref": CONTRACT_CLEAN_REF,
            "source_language": "zh",
            "target_language": target_language,
            "target_platform": "TikTok",
            "variation_target_count": str(variation_target_count),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    location = response.headers["location"]
    assert location.startswith("/tasks/")
    return location.split("/tasks/", 1)[1].split("?", 1)[0]


def _ls_ref(refs: list[dict[str, Any]], ref_id: str) -> dict[str, Any]:
    for ref in refs:
        if ref.get("ref_id") == ref_id:
            return ref
    raise AssertionError(f"ref_id {ref_id!r} not present in {[r.get('ref_id') for r in refs]}")


# --- §1. Persisted packet carries populated deltas on both mirrors ----


def test_post_persists_packet_with_populated_ls_deltas(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    assert stored is not None
    assert stored["kind"] == "matrix_script"

    # Both mirrors carry the deltas.
    for mirror_name, refs in (
        ("packet.line_specific_refs", stored["packet"]["line_specific_refs"]),
        ("top-level line_specific_refs", stored["line_specific_refs"]),
    ):
        var_ref = _ls_ref(refs, "matrix_script_variation_matrix")
        slot_ref = _ls_ref(refs, "matrix_script_slot_pack")
        assert "delta" in var_ref, f"{mirror_name} LS1 delta missing"
        assert "delta" in slot_ref, f"{mirror_name} LS2 delta missing"
        assert var_ref["delta"]["axis_kind_set"] == [
            "categorical",
            "range",
            "enum",
        ]
        assert len(var_ref["delta"]["axes"]) == 3
        assert len(var_ref["delta"]["cells"]) == 4
        assert slot_ref["delta"]["slot_kind_set"] == [
            "primary",
            "alternate",
            "fallback",
        ]
        assert len(slot_ref["delta"]["slots"]) == 4


def test_persisted_round_trip_cells_to_slots_resolves(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    refs = stored["packet"]["line_specific_refs"]
    cells = _ls_ref(refs, "matrix_script_variation_matrix")["delta"]["cells"]
    slots = _ls_ref(refs, "matrix_script_slot_pack")["delta"]["slots"]
    slot_ids = {s["slot_id"] for s in slots}
    cell_ids = {c["cell_id"] for c in cells}
    for cell in cells:
        assert cell["script_slot_ref"] in slot_ids
    for slot in slots:
        assert slot["binds_cell_id"] in cell_ids


# --- §2. Projector consumes authored delta -----------------------------


def test_projector_consumes_authored_delta(monkeypatch):
    from gateway.app.services.matrix_script.workbench_variation_surface import (
        project_workbench_variation_surface,
    )

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    projected = project_workbench_variation_surface(stored["packet"])
    assert len(projected["variation_plan"]["axes"]) == 3
    assert len(projected["variation_plan"]["cells"]) == 4
    assert len(projected["copy_bundle"]["slots"]) == 4

    slot_ids = {s["slot_id"] for s in projected["copy_bundle"]["slots"]}
    for cell in projected["variation_plan"]["cells"]:
        assert cell["script_slot_ref"] in slot_ids


# --- §3. Rendered HTML carries authored axes / cells / slots ---------


def test_get_workbench_renders_real_axes_cells_slots(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
        response = client.get(
            f"/tasks/{task_id}",
            params={"created": "matrix_script"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.text

    # Phase B mount markers from §8.B remain in force.
    assert 'data-role="matrix-script-variation-panel"' in body
    assert 'data-panel-kind="matrix_script"' in body
    assert "matrix_script_workbench_variation_surface_v1" in body

    # All four cell / slot ids surface in the rendered HTML.
    for i in (1, 2, 3, 4):
        assert f"cell_{i:03d}" in body, f"cell_{i:03d} missing from HTML"
        assert f"slot_{i:03d}" in body, f"slot_{i:03d} missing from HTML"

    # Canonical axis ids surface.
    for axis_id in ("tone", "audience", "length"):
        assert axis_id in body

    # At least one tone value and one audience value appear.
    assert any(tone in body for tone in TONES)
    assert any(aud in body for aud in AUDIENCES)

    # Empty-fallback messages MUST NOT render — the §8.C goal is to
    # eliminate exactly this branch.
    assert "No axes resolved on this packet" not in body
    assert "No cells resolved on this packet" not in body
    assert "No slots resolved on this packet" not in body
    assert "No `line_specific_refs[]` on this packet" not in body

    # §8.G regression: the dict-method bound-callable repr leaked when
    # the template wrote ``axis.values`` (Jinja attribute access resolved
    # to ``dict.values`` before falling back to the ``"values"`` key).
    # The fix uses ``axis["values"]`` item access; assert the broken repr
    # is absent anywhere in the body.
    assert "<built-in method values" not in body


# --- §3.G Axes-table renders human-readable axis values -----------


def test_axes_table_renders_human_readable_values(monkeypatch):
    """§8.G regression: the Axes table values column must render the
    actual axis values (``formal``/``casual``/``playful`` for tone,
    ``b2b``/``b2c``/``internal`` for audience, ``min=…/max=…/step=…``
    for length), not the dict's bound ``values()`` method repr.

    Scoped to the axes-table region between the ``<h3>Axes</h3>``
    heading and the ``<h3>Cells × Slots</h3>`` heading so cell-level
    ``axis_selections`` (which also surface tone/audience tokens
    elsewhere on the page) cannot mask a broken axes-row render.
    """
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
        response = client.get(
            f"/tasks/{task_id}",
            params={"created": "matrix_script"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.text

    axes_heading = '<h3 style="margin:12px 0 6px;">Axes</h3>'
    cells_heading = '<h3 style="margin:16px 0 6px;">Cells × Slots</h3>'
    assert axes_heading in body, "Axes heading missing from rendered HTML"
    assert cells_heading in body, "Cells × Slots heading missing from rendered HTML"
    axes_start = body.index(axes_heading)
    axes_end = body.index(cells_heading, axes_start)
    axes_region = body[axes_start:axes_end]

    # Tone (categorical) — every value renders inside the axes table.
    for tone in TONES:
        assert tone in axes_region, (
            f"tone value {tone!r} missing from axes table region"
        )

    # Audience (enum) — every value renders inside the axes table.
    for aud in AUDIENCES:
        assert aud in axes_region, (
            f"audience value {aud!r} missing from axes table region"
        )

    # Length (range) — the mapping branch must render
    # min/max/step from the dict, not the bound ``values()`` method repr.
    assert f"min={LENGTH_RANGE['min']}" in axes_region
    assert f"max={LENGTH_RANGE['max']}" in axes_region
    assert f"step={LENGTH_RANGE['step']}" in axes_region

    # Negative: the broken Jinja attribute-vs-item access bug is gone.
    assert "<built-in method values" not in axes_region
    assert "<built-in method values" not in body


# --- §3.E Shared shell suppresses Hot Follow controls on matrix_script -


def test_matrix_script_workbench_does_not_render_hot_follow_shell_controls(
    monkeypatch,
):
    """§8.E regression: the shared workbench shell must not render Hot
    Follow stage cards / pipeline summary / dub-engine selectors /
    Burmese-specific deliverable rows / subtitle-track meta row when
    ``task.kind != "hot_follow"``.

    The check is a closed token list drawn from the follow-up blocker
    review v1 §5 ("Required correction type") — every token is a
    visible Hot Follow control. The Matrix Script Phase B variation
    panel and the generic operator surface strip remain mounted (and
    are asserted by the dispatch / render context cases above), so the
    operator-visible result is "the shared shell + the Matrix Script
    panel" with **no** Hot Follow controls bleeding through.

    Scope note: ``<script>`` blocks are stripped before assertion
    because the shared topbar inlines the global ``window.__I18N__``
    translation dictionary, and that dictionary necessarily contains
    Hot Follow string keys (``workbench.mm_audio`` → "Burmese audio",
    etc.). Those keys are not operator-visible controls — they are
    JavaScript translation strings — so the regression scope is the
    **visible HTML body**, not the inlined translation payload.
    """
    import re

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
        response = client.get(
            f"/tasks/{task_id}",
            params={"created": "matrix_script"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.text

    # The Matrix Script panel still mounts (kept here as a positive
    # anchor so the negative assertions below cannot pass on an empty
    # render).
    assert 'data-role="matrix-script-variation-panel"' in body
    assert 'data-panel-kind="matrix_script"' in body

    # Strip <script>...</script> blocks so the inlined i18n payload
    # (window.__I18N__) and the matrix_script-side currentTask dump
    # (window.currentTask, but only inside Hot Follow gate now) don't
    # mask the test of the visible HTML surface.
    visible_html = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Hot Follow pipeline summary tokens — the labels visible on the
    # original mixed render.
    forbidden_pipeline_tokens = (
        "whisper+gemini",
        "auto-fallback",
    )

    # Hot Follow stage cards — the parse / subtitle / dub / pack DOM ids
    # that anchor the Hot Follow steps panel.
    forbidden_stage_dom = (
        'id="btn-parse"',
        'id="btn-dub"',
        'id="btn-pack"',
        'id="btn-subtitles"',
        'id="btn-scenes"',
        'id="hard-subtitles-toggle"',
        'id="voice-id"',
        'id="dub-provider"',
        'id="parse-status"',
        'id="dub-status"',
        'id="pack-status"',
        'id="subs-status"',
        'id="audio-preview"',
        'id="debug-panel"',
    )

    # Hot Follow deliverable strip — Burmese-specific deliverable
    # filenames and download endpoints.
    forbidden_deliverables = (
        "mm.srt",
        "mm.txt",
        "origin.srt",
        "mm_audio",
        "/v1/tasks/",
    )

    for token in forbidden_pipeline_tokens:
        assert token not in visible_html, (
            f"Hot Follow pipeline token {token!r} leaked into matrix_script visible render"
        )
    for token in forbidden_stage_dom:
        assert token not in visible_html, (
            f"Hot Follow stage DOM {token!r} leaked into matrix_script visible render"
        )
    for token in forbidden_deliverables:
        assert token not in visible_html, (
            f"Hot Follow deliverable token {token!r} leaked into matrix_script visible render"
        )

    # Workbench i18n keys for the Hot Follow stage / deliverable / publish
    # / debug sections — none of these labels should resolve in the
    # visible HTML. They are still present in the inlined translation
    # payload (which is the responsibility of the i18n bundle, not
    # the workbench shell), so we assert against ``visible_html`` only.
    forbidden_i18n_labels = (
        "workbench.deliverables",
        "workbench.scenes_section",
        "workbench.publish_hub",
        "workbench.steps",
        "workbench.step.parse",
        "workbench.step.dub",
        "workbench.step.pack",
        "workbench.step.subtitles",
        "workbench.meta.subtitle_track",
        "workbench.meta.pipeline",
        "workbench.logs",
    )
    for token in forbidden_i18n_labels:
        assert token not in visible_html, (
            f"Hot Follow i18n label {token!r} leaked into matrix_script visible render"
        )


# --- §4. Cardinality at boundaries ----------------------------------


@pytest.mark.parametrize("k", [1, 12])
def test_persisted_cells_cardinality_matches_variation_target_count(
    monkeypatch, k
):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=k)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    refs = stored["packet"]["line_specific_refs"]
    cells = _ls_ref(refs, "matrix_script_variation_matrix")["delta"]["cells"]
    slots = _ls_ref(refs, "matrix_script_slot_pack")["delta"]["slots"]
    assert len(cells) == k
    assert len(slots) == k
    # Body refs are still opaque and step-aligned at the boundaries.
    for slot in slots:
        assert slot["body_ref"].startswith("content://matrix-script/")
        assert slot["length_hint"] in LENGTH_PICKS


# --- §5. Slot language_scope carries entry target language --------


@pytest.mark.parametrize("target_language", ["mm", "vi"])
def test_slot_language_scope_uses_entry_target_language(
    monkeypatch, target_language
):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(
            client,
            variation_target_count=2,
            target_language=target_language,
        )
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    refs = stored["packet"]["line_specific_refs"]
    slots = _ls_ref(refs, "matrix_script_slot_pack")["delta"]["slots"]
    for slot in slots:
        assert slot["language_scope"] == {
            "source_language": "zh",
            "target_language": [target_language],
        }


# --- §6. §8.A guard remains in force on the §8.C sample ---------


def test_source_script_ref_remains_opaque_on_phase_b_sample(monkeypatch):
    """§8.C must not regress §8.A. The fresh sample's persisted source
    ref MUST be the opaque value the operator submitted — never the body
    ref synthesised by Phase B authoring.
    """
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client)
    finally:
        app.dependency_overrides.clear()

    stored = repo.get(task_id)
    assert stored["source_url"] == CONTRACT_CLEAN_REF
    assert stored["config"]["entry"]["source_script_ref"] == CONTRACT_CLEAN_REF
    # The synthesised body_refs MUST NOT equal the operator-supplied
    # source_script_ref — bodies are opaque and per-slot.
    refs = stored["packet"]["line_specific_refs"]
    slots = _ls_ref(refs, "matrix_script_slot_pack")["delta"]["slots"]
    for slot in slots:
        assert slot["body_ref"] != CONTRACT_CLEAN_REF
        assert task_id in slot["body_ref"]


# --- §7. §8.B dispatch markers remain in force ------------------


def test_panel_kind_dispatch_unchanged_under_phase_b_authoring(monkeypatch):
    """The §8.B dispatch resolver MUST still emit
    ``panel_kind="matrix_script"`` and surface both ref_ids when the
    packet now also carries delta payloads.
    """
    from gateway.app.services.operator_visible_surfaces.projections import (
        PANEL_REF_DISPATCH,
        resolve_line_specific_panel,
    )

    assert PANEL_REF_DISPATCH["matrix_script_variation_matrix"] == "matrix_script"
    assert PANEL_REF_DISPATCH["matrix_script_slot_pack"] == "matrix_script"

    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client)
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


# --- §8. Render-context capture (variation surface attached) -----


def test_workbench_render_context_attaches_variation_surface(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    captured: dict[str, Any] = {}

    real_render = tasks_router.render_template

    def capturing_render(*, request, name, ctx=None, status_code=200, headers=None):
        captured["template"] = name
        ws = (
            ((ctx or {}).get("task_json", {}) or {})
            .get("operator_surfaces", {})
            .get("workbench", {})
        )
        captured["panel_kind"] = ws.get("line_specific_panel", {}).get("panel_kind")
        surface = ws.get("matrix_script_variation_surface")
        captured["surface_attached"] = surface is not None
        if surface:
            captured["axes_count"] = len(surface["variation_plan"]["axes"])
            captured["cells_count"] = len(surface["variation_plan"]["cells"])
            captured["slots_count"] = len(surface["copy_bundle"]["slots"])
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
        task_id = _post_fresh_sample(client, variation_target_count=4)
        response = client.get(f"/tasks/{task_id}", params={"created": "matrix_script"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured["template"] == "task_workbench.html"
    assert captured["panel_kind"] == "matrix_script"
    assert captured["surface_attached"] is True
    assert captured["axes_count"] == 3
    assert captured["cells_count"] == 4
    assert captured["slots_count"] == 4


# --- §9. MS-W3 taxonomy values render (live 500 incident regression) ---


def test_ms_w3_script_structure_taxonomy_values_render(monkeypatch):
    """Live incident regression: the MS-W3 script-structure read-view
    block in ``task_workbench.html`` iterated over ``tax.values`` —
    Jinja's attribute access on a dict whose key is named ``values``
    resolves to the bound ``dict.values`` method (not the dict's
    ``"values"`` key) and the for-loop raises
    ``TypeError: 'builtin_function_or_method' object is not iterable``,
    turning every Matrix Script task page into a 500.

    Same shape as the §8.G axis-values fix; the patch flips the access
    to ``tax["values"]``. This test asserts both that the page no
    longer 500s AND that the resolved-keywords taxonomy values surface
    inside the script-structure region (i.e. the loop actually runs
    over the dict's ``"values"`` list and not the bound method).
    """
    monkeypatch.setenv("AUTH_MODE", "off")
    repo = _InMemoryRepo()
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    try:
        task_id = _post_fresh_sample(client, variation_target_count=4)
        response = client.get(
            f"/tasks/{task_id}",
            params={"created": "matrix_script"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.text

    # Script-structure region must be present (positive anchor).
    assert 'data-role="matrix-script-script-structure-panel"' in body
    assert 'data-role="ms-script-structure-taxonomy-item"' in body

    # Forbidden-terms taxonomy is always resolved (vendor / model /
    # provider / engine red lines, per script_structure_view._derive_
    # forbidden_taxonomy). Each value MUST appear inside the rendered
    # taxonomy region — proves the for-loop iterates over the dict's
    # ``"values"`` list, not the bound ``dict.values`` method.
    forbidden_marker = (
        'data-role="ms-script-structure-taxonomy-item" '
        'data-taxonomy-id="forbidden_terms"'
    )
    assert forbidden_marker in body
    forbidden_start = body.index(forbidden_marker)
    forbidden_end = body.index("</div>", forbidden_start)
    forbidden_region = body[forbidden_start:forbidden_end]
    for forbidden_value in ("vendor", "model", "provider", "engine"):
        assert f">{forbidden_value}<" in forbidden_region, (
            f"forbidden taxonomy value {forbidden_value!r} missing — Jinja "
            f"`tax.values` likely resolved to the bound dict.values method"
        )

    # Negative: the bound-method repr must not leak into the taxonomy
    # region (the same canary used by the §8.G axes-table regression).
    assert "<built-in method values" not in body

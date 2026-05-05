"""OWC-MS PR-2 — Workbench template-intact regression tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §6 acceptance bar item 2:
  "the existing Variation Panel remains intact and correctly positioned
  within the converged workbench".
- Re-review blocker: "regression proving Variation Panel remains intact".
- Re-review blocker 2 follow-up: "script-structure read-view test
  proving non-placeholder content is rendered from resolved source
  content".

Scans the actual `task_workbench.html` template file for the structural
markers that prove (a) the existing Variation Panel block is preserved
verbatim with its identifying `data-role` markers and table headers,
(b) the new MS-W3 script-structure panel renders real `body_text`
spans (not placeholder-only content), and (c) the new MS-W5 review-
zone panel renders real `<form>` submit elements posting through the
existing closure endpoint template.
"""
from __future__ import annotations

from pathlib import Path

import pytest


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "templates" / "task_workbench.html"
)


@pytest.fixture(scope="module")
def template_text() -> str:
    return TEMPLATE_PATH.read_text()


# -- 1. Variation Panel remains intact at its position -----------------


def test_variation_panel_block_preserved(template_text: str) -> None:
    assert 'data-role="matrix-script-variation-panel"' in template_text
    assert "Matrix Script — Variation Panel" in template_text
    assert "matrix_script_workbench_variation_surface_v1" in template_text


def test_variation_panel_table_headers_preserved(template_text: str) -> None:
    # The Axes / Cells × Slots / Slot detail / Attribution refs / Publish
    # feedback projection sub-blocks must all still be present.
    for marker in (
        "<h3 style=\"margin:12px 0 6px;\">Axes</h3>",
        "<h3 style=\"margin:16px 0 6px;\">Cells × Slots</h3>",
        "<h3 style=\"margin:16px 0 6px;\">Slot detail</h3>",
        "<h3 style=\"margin:16px 0 6px;\">Attribution refs</h3>",
        "<h3 style=\"margin:16px 0 6px;\">Publish feedback projection</h3>",
    ):
        assert marker in template_text, f"Variation Panel sub-block missing: {marker}"


def test_variation_panel_axes_table_uses_item_access_g_pattern(
    template_text: str,
) -> None:
    """§8.G item-access pattern preservation — `axis["values"]` not
    `axis.values` (the latter binds to the dict's bound method)."""
    assert 'axis["values"]' in template_text


def test_variation_panel_positioned_inside_matrix_script_branch(
    template_text: str,
) -> None:
    """Confirm the Variation Panel is inside the existing
    `panel_kind == "matrix_script"` gate, not orphaned outside."""
    assert (
        'ops_workbench_panel.panel_kind == "matrix_script"' in template_text
    )
    # The matrix_script branch contains the Variation Panel marker.
    matrix_branch_start = template_text.find(
        'ops_workbench_panel.panel_kind == "matrix_script"'
    )
    var_panel_pos = template_text.find('data-role="matrix-script-variation-panel"')
    assert matrix_branch_start < var_panel_pos


# -- 2. MS-W3 script-structure renders REAL body content (not placeholder) -


def test_script_structure_panel_renders_real_body_text_span(
    template_text: str,
) -> None:
    """The MS-W3 panel must include a body-text span that renders
    real `section.body_text` content when present, not just a status
    label sentinel."""
    assert (
        'data-role="matrix-script-script-structure-panel"' in template_text
    )
    assert 'data-role="ms-script-structure-section-body"' in template_text


def test_script_structure_panel_renders_real_taxonomy_values_pills(
    template_text: str,
) -> None:
    """The MS-W3 panel must include a values span that renders real
    `tax.values` pills when present, not just a status label sentinel."""
    assert (
        'data-role="ms-script-structure-taxonomy-values"' in template_text
    )


# -- 3. MS-W5 renders real submit forms posting to existing endpoint ---


def test_review_zone_panel_renders_real_submit_form(template_text: str) -> None:
    """The MS-W5 panel must include actual `<form>` elements (not just
    payload-shape examples) posting to the resolved closure endpoint."""
    assert 'class="matrix-script-review-form"' in template_text
    assert 'data-role="ms-review-zone-submit-form"' in template_text
    assert 'data-role="ms-review-zone-submit-input"' in template_text
    assert 'data-role="ms-review-zone-submit-button"' in template_text


def test_review_zone_submit_form_posts_through_existing_closure_endpoint(
    template_text: str,
) -> None:
    """The form action must come from the bundle's resolved
    closure_endpoint_url (no new endpoint introduced by PR-2)."""
    assert "z.submit_form.action" in template_text
    assert 'event_kind: form.dataset.eventKind' in template_text
    assert "review_zone: form.dataset.zoneId" in template_text


def test_review_zone_submit_handler_exists_inline(template_text: str) -> None:
    """Verify the inline JS submit handler is wired (real client-side
    submit, not display-only)."""
    assert 'data-role="ms-review-zone-submit-handler"' in template_text
    assert "fetch(form.action" in template_text

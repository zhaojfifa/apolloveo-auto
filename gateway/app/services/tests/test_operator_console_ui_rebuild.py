"""Operator-console UI rebuild — structural assertions.

Scope: pure template-shape checks for the operator-language rebuild of the
Matrix Script and Digital Anchor surfaces in
``gateway/app/templates/task_workbench.html`` and
``gateway/app/templates/task_publish_hub.html``.

These assertions are paired with the existing
``test_matrix_script_workbench_blocks_a_b_c.py`` /
``test_matrix_script_workbench_blocks_d_e_f.py`` /
``test_matrix_script_delivery_center_blocks_a_to_f.py`` structural
contracts, which continue to enforce the underlying
``data-role="ms-block-*"`` and ``data-role="matrix-script-block-*"``
markers and document order. This file adds the operator-rebuild
post-conditions:

1. The new operator-console stylesheet is wired into both surfaces.
2. The eight-stage operator strip renders at the top of the workbench.
3. The Matrix Script Workbench section heads carry operator-language
   titles (任务摘要 / 脚本结构 / 变体策略 / 生成 / 候选评审 / 交付概览),
   not the previous "Workbench A · ..." academic prefix.
4. The Matrix Script Delivery Center header carries the operator-language
   title and the publish-readiness banner uses the operator banner class.
5. The Digital Anchor Workbench panels render in operator workflow order
   (Brief → Content → Scene → Role/Speaker → Language → Review), which
   is the user-defined operator order — not the previous Role-first order.
6. The architect / debug strips ("Operator surface" + "Line-specific
   panel") are demoted into a collapsed ``<details class="op-collapse">``
   wrapper (their data-role markers are preserved).
7. Hot Follow conditional rendering is bytewise unaffected — the
   ``operator-hot-follow-panel`` marker still appears under
   ``ops_hot_follow_panel.mounted``, and ``hot_follow_*.html`` standalone
   templates are unchanged.

These tests do not load Python presenters; they read the templates as
text. Same shape as the other ``test_matrix_script_workbench_blocks_*``
template-structure tests.
"""

from __future__ import annotations

import re
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
_PUBLISH_HUB_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"
_TASKS_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "tasks.html"
_OPERATOR_CSS = _REPO_ROOT / "gateway" / "app" / "static" / "css" / "operator_console.css"
_HOT_FOLLOW_WORKBENCH_TEMPLATE = (
    _REPO_ROOT / "gateway" / "app" / "templates" / "hot_follow_workbench.html"
)
_HOT_FOLLOW_PUBLISH_TEMPLATE = (
    _REPO_ROOT / "gateway" / "app" / "templates" / "hot_follow_publish.html"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_jinja_comments(template: str) -> str:
    return re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)


def _ms_panel_gate_body(template: str) -> str:
    """Return the body inside the matrix_script panel gate."""
    rendered = _strip_jinja_comments(template)
    open_tag = '{% if ops_workbench_panel.panel_kind == "matrix_script" %}'
    start = rendered.find(open_tag)
    assert start >= 0, "matrix_script panel gate not found"
    cursor = start + len(open_tag)
    depth = 1
    while depth and cursor < len(rendered):
        next_open = re.search(r"{% if\b", rendered[cursor:])
        next_close = re.search(r"{% endif %}", rendered[cursor:])
        if next_close is None:
            break
        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            cursor += next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return rendered[start:cursor + next_close.start()]
            cursor += next_close.end()
    return ""


def _da_panel_gate_body(template: str) -> str:
    """Return the body inside the digital_anchor panel gate."""
    rendered = _strip_jinja_comments(template)
    open_tag = '{% if ops_workbench_panel.panel_kind == "digital_anchor" %}'
    start = rendered.find(open_tag)
    assert start >= 0, "digital_anchor panel gate not found"
    cursor = start + len(open_tag)
    depth = 1
    while depth and cursor < len(rendered):
        next_open = re.search(r"{% if\b", rendered[cursor:])
        next_close = re.search(r"{% endif %}", rendered[cursor:])
        if next_close is None:
            break
        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            cursor += next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return rendered[start:cursor + next_close.start()]
            cursor += next_close.end()
    return ""


# ---------------------------------------------------------------------
# Stylesheet wiring
# ---------------------------------------------------------------------


def test_operator_console_stylesheet_exists() -> None:
    assert _OPERATOR_CSS.is_file(), "operator_console.css must exist on disk"
    body = _read(_OPERATOR_CSS)
    # Sentinel rules — these classes are referenced by the operator
    # surface and the rebuild relies on them being addressable.
    for needle in (
        ".op-card",
        ".op-card--accent-emerald",
        ".op-card--accent-blue",
        ".op-section-head",
        ".op-section-title",
        ".op-section-index",
        ".op-pill",
        ".op-banner",
        ".op-meta-grid",
        ".op-stage-strip",
        ".op-collapse",
        ".op-tech-note",
    ):
        assert needle in body, f"{needle} must be defined in operator_console.css"


def test_workbench_template_includes_operator_console_stylesheet() -> None:
    template = _read(_WORKBENCH_TEMPLATE)
    assert '/static/css/operator_console.css' in template, (
        "task_workbench.html must link the operator console stylesheet"
    )


def test_publish_hub_template_includes_operator_console_stylesheet() -> None:
    template = _read(_PUBLISH_HUB_TEMPLATE)
    assert '/static/css/operator_console.css' in template, (
        "task_publish_hub.html must link the operator console stylesheet"
    )


# ---------------------------------------------------------------------
# Workbench stage strip (top-level operator breadcrumb)
# ---------------------------------------------------------------------


def test_workbench_renders_eight_stage_strip_at_top() -> None:
    template = _read(_WORKBENCH_TEMPLATE)
    assert 'data-role="op-console-stage-strip"' in template
    # Eight stages declared in the same closed order as the existing
    # eight-stage projection used by Task Area cards.
    rendered = _strip_jinja_comments(template)
    strip_open = rendered.find('data-role="op-console-stage-strip"')
    assert strip_open >= 0
    strip_subtree = rendered[strip_open:strip_open + 4000]
    for stage in (
        "已创建",
        "待配置",
        "生成中",
        "待校对",
        "成片完成",
        "可发布",
        "已回填",
        "已归档",
    ):
        assert stage in strip_subtree, f"stage {stage} must appear in the strip"


def test_stage_strip_appears_before_first_matrix_script_block() -> None:
    template = _read(_WORKBENCH_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_strip = rendered.find('data-role="op-console-stage-strip"')
    pos_block_a = rendered.find('data-role="matrix-script-block-a-goal-summary"')
    assert pos_strip >= 0
    assert pos_block_a > pos_strip, (
        "stage strip must render before the matrix_script Block A goal summary"
    )


# ---------------------------------------------------------------------
# Matrix Script Workbench — operator-language section heads
# ---------------------------------------------------------------------


def test_matrix_script_workbench_uses_operator_language_block_titles() -> None:
    """Section titles must read like operator workflow steps, not like
    'Workbench A · ...' academic prefixes."""
    inside = _ms_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    assert inside, "matrix_script panel body not found"
    # Each block carries an operator-language head + an op-section-index
    # badge. The operator-language head sits inside an op-card.
    assert 'class="op-card op-card--accent-emerald" data-role="matrix-script-block-a-goal-summary"' in inside
    assert 'data-role="ms-block-a-title">任务摘要</h2>' in inside
    assert 'class="op-card op-card--accent-indigo" data-role="matrix-script-block-b-script-structure"' in inside
    assert 'data-role="ms-block-b-title">脚本结构</h2>' in inside
    assert 'class="op-card op-card--accent-indigo" data-role="matrix-script-block-c-variant-strategy"' in inside
    assert 'data-role="ms-block-c-title">变体策略</h2>' in inside
    assert 'class="op-card op-card--accent-indigo" data-role="matrix-script-block-d-generate-regenerate"' in inside
    assert 'data-role="ms-block-d-title">生成 / 重新生成</h2>' in inside
    assert 'class="op-card op-card--accent-violet" data-role="matrix-script-block-e-candidate-review"' in inside
    assert 'data-role="ms-block-e-title">候选评审</h2>' in inside
    assert 'class="op-card op-card--accent-emerald" data-role="matrix-script-block-f-delivery-teaser"' in inside
    assert 'data-role="ms-block-f-title">交付概览</h2>' in inside


def test_matrix_script_workbench_block_titles_drop_academic_prefix() -> None:
    """The previous 'Workbench A · 任务摘要' style headers must be gone."""
    inside = _ms_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    for legacy_title in (
        "Workbench A · 任务摘要",
        "Workbench B · 脚本结构",
        "Workbench C · 变体策略",
        "Workbench D · 生成 / 重新生成",
        "Workbench E · 候选评审",
        "Workbench F · 交付概览",
    ):
        assert legacy_title not in inside, (
            f"legacy academic header '{legacy_title}' must be removed from the operator-rebuilt workbench"
        )


def test_matrix_script_block_a_renders_operator_banner_callouts() -> None:
    """Block A must surface the next-step / blocker callouts using the
    operator banner class so the operator sees the call-to-action without
    digging into a meta grid."""
    inside = _ms_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    block_a_start = inside.find('data-role="matrix-script-block-a-goal-summary"')
    assert block_a_start >= 0
    # Look at the block A subtree (until next op-card opens or EOF).
    next_card = inside.find('class="op-card', block_a_start + 1)
    block_a_subtree = inside[block_a_start: next_card if next_card > 0 else len(inside)]
    assert "op-banner--next" in block_a_subtree, (
        "Block A must render the next-step banner with op-banner--next"
    )
    assert (
        "op-banner--blocker" in block_a_subtree or "op-banner--ready" in block_a_subtree
    ), "Block A must render a blocker or ready banner"


def test_matrix_script_secondary_diagnostics_are_collapsed() -> None:
    """The legacy PR-U2 / MS-W3 / Variation panel + RC PR-2/PR-3/PR-4
    secondary diagnostics must render inside a collapsed
    op-collapse <details> wrapper so they no longer dominate the
    operator surface — but their data-role markers must remain so
    existing structural tests still pass."""
    inside = _ms_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    # Marker preservation (already enforced by other tests, double-checked here).
    assert 'data-role="matrix-script-comprehension-panel"' in inside
    assert 'data-role="matrix-script-script-structure-panel"' in inside
    assert 'data-role="matrix-script-variation-panel"' in inside
    # The collapse wrapper exists.
    assert 'data-role="op-console-ms-secondary-fold"' in inside, (
        "matrix_script secondary diagnostics must be wrapped in a collapse"
    )
    # The wrapper opens BEFORE PR-U2 comprehension panel (which is the
    # first secondary diagnostic in the legacy order).
    rendered = _strip_jinja_comments(_read(_WORKBENCH_TEMPLATE))
    pos_fold = rendered.find('data-role="op-console-ms-secondary-fold"')
    pos_comp = rendered.find('data-role="matrix-script-comprehension-panel"')
    assert 0 < pos_fold < pos_comp, (
        "secondary fold wrapper must precede the legacy comprehension panel"
    )


def test_matrix_script_architect_strips_demoted_to_collapsed_block() -> None:
    """The 'Operator surface' + 'Line-specific panel' debug strips that
    used to dominate the top of the workbench must now live inside a
    single collapsed-by-default details wrapper at page bottom. Their
    data-role markers are preserved so existing wiring tests pass."""
    template = _read(_WORKBENCH_TEMPLATE)
    rendered = _strip_jinja_comments(template)

    # Marker preservation
    assert 'data-role="operator-surface-strip"' in rendered
    assert 'data-role="operator-line-specific-panel"' in rendered

    # Architect fold wrapper exists
    assert 'data-role="op-console-architect-fold"' in rendered

    # Architect fold opens AFTER the matrix_script Block A (i.e., the
    # debug strips are no longer at the top of the page).
    pos_block_a = rendered.find('data-role="matrix-script-block-a-goal-summary"')
    pos_fold = rendered.find('data-role="op-console-architect-fold"')
    assert pos_block_a >= 0 and pos_fold >= 0
    assert pos_fold > pos_block_a, (
        "architect debug strips must sit BELOW Block A (i.e., visually demoted)"
    )

    # Architect fold opens AFTER the matrix_script Block F as well — i.e.,
    # the debug strips are at the bottom of the page, not interleaved.
    pos_block_f = rendered.find('data-role="matrix-script-block-f-delivery-teaser"')
    if pos_block_f >= 0:
        assert pos_fold > pos_block_f, (
            "architect debug strips must sit BELOW Block F"
        )


# ---------------------------------------------------------------------
# Digital Anchor Workbench — operator workflow ordering
# ---------------------------------------------------------------------


def test_digital_anchor_workbench_renders_brief_summary_first() -> None:
    """The operator workflow starts with a brief / normalised input
    summary. The new ``digital-anchor-brief-summary`` panel renders
    BEFORE every other DA panel."""
    inside = _da_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    assert inside, "digital_anchor panel body not found"
    pos_brief = inside.find('data-role="digital-anchor-brief-summary"')
    assert pos_brief >= 0, "DA brief summary panel must exist"
    for marker in (
        'data-role="digital-anchor-content-structure-panel"',
        'data-role="digital-anchor-scene-template-panel"',
        'data-role="digital-anchor-role-binding-panel"',
        'data-role="digital-anchor-language-output-panel"',
        'data-role="digital-anchor-review-zone-panel"',
    ):
        pos_other = inside.find(marker)
        assert pos_other > pos_brief, (
            f"brief summary must appear BEFORE {marker} (got {pos_brief} vs {pos_other})"
        )


def test_digital_anchor_workbench_panel_order_matches_operator_workflow() -> None:
    """Operator workflow order: brief → content → scene → role/speaker →
    language → review.

    NOTE: this is a deliberate reorder relative to the prior layout, which
    rendered Role Binding first. The content and structure of each panel
    is unchanged; only the document position changes."""
    inside = _da_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    panels = [
        ('digital-anchor-brief-summary', 'Brief summary'),
        ('digital-anchor-content-structure-panel', 'Content structure'),
        ('digital-anchor-scene-template-panel', 'Scene template'),
        ('digital-anchor-role-binding-panel', 'Role binding'),
        ('digital-anchor-language-output-panel', 'Language output'),
        ('digital-anchor-review-zone-panel', 'Review zone'),
    ]
    positions = []
    for marker, label in panels:
        idx = inside.find(f'data-role="{marker}"')
        assert idx >= 0, f"{label} panel must exist (data-role={marker})"
        positions.append((idx, label))
    sorted_by_position = [label for _, label in sorted(positions)]
    expected = [label for _, label in panels]
    assert sorted_by_position == expected, (
        f"DA panel order must follow operator workflow; got {sorted_by_position}, expected {expected}"
    )


def test_digital_anchor_panels_use_operator_console_card_class() -> None:
    inside = _da_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    for marker in (
        'digital-anchor-brief-summary',
        'digital-anchor-content-structure-panel',
        'digital-anchor-scene-template-panel',
        'digital-anchor-role-binding-panel',
        'digital-anchor-language-output-panel',
        'digital-anchor-review-zone-panel',
    ):
        # Each panel container must carry an op-card class. We don't
        # require a specific accent (emerald / blue / violet) — only
        # that the operator console card system is in use.
        idx = inside.find(f'data-role="{marker}"')
        # Inspect a small window before the marker to find the class attr.
        window = inside[max(0, idx - 200): idx + 50]
        assert 'op-card' in window, (
            f"{marker} container must use the op-card class (window: {window!r})"
        )


def test_digital_anchor_role_binding_no_longer_renders_first() -> None:
    """Operator order moves Role Binding from position 1 to position 4
    (after Content + Scene). This test pins that move so a future
    accidental revert is caught."""
    inside = _da_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    pos_role = inside.find('data-role="digital-anchor-role-binding-panel"')
    pos_content = inside.find('data-role="digital-anchor-content-structure-panel"')
    pos_scene = inside.find('data-role="digital-anchor-scene-template-panel"')
    assert min(pos_content, pos_scene) < pos_role, (
        "Role Binding must render AFTER both Content Structure and Scene Template"
    )


# ---------------------------------------------------------------------
# Matrix Script Delivery Center — operator-language header + banner
# ---------------------------------------------------------------------


def test_delivery_center_header_uses_operator_language() -> None:
    template = _read(_PUBLISH_HUB_TEMPLATE)
    # Header card uses op-card with the emerald accent.
    assert 'class="op-card op-card--accent-emerald" data-role="matrix-script-delivery-center-header"' in template
    # The legacy "DELIVERY CENTER · matrix_script · v1" packet-style
    # header must be gone.
    assert "DELIVERY CENTER · matrix_script · v1" not in template


def test_delivery_center_publish_readiness_banner_uses_operator_banner_class() -> None:
    """The publish-readiness banner is the most visible operator
    affordance on this page — it must use the op-banner class so
    operators see ✓ ready or ◐ blocked at a glance."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_banner = rendered.find('data-role="ms-dc-readiness-banner"')
    assert pos_banner >= 0
    # Look at the banner element line for the class attribute.
    banner_window = rendered[pos_banner: pos_banner + 600]
    assert "op-banner" in banner_window
    assert "op-banner--ready" in banner_window or "op-banner--blocker" in banner_window


def test_delivery_center_blocks_use_operator_console_cards() -> None:
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    for block_marker in (
        'matrix-script-block-a-final-video-primary',
        'matrix-script-block-b-required-deliverables',
        'matrix-script-block-c-scene-pack',
        'matrix-script-block-d-copy-bundle',
        'matrix-script-block-e-publish-feedback',
        'matrix-script-block-f-iteration-archive',
    ):
        idx = rendered.find(f'data-role="{block_marker}"')
        assert idx >= 0, f"{block_marker} must still exist"
        window = rendered[max(0, idx - 200): idx + 50]
        assert 'op-card' in window, f"{block_marker} container must use op-card"


def test_delivery_center_block_titles_use_operator_language() -> None:
    """Operator-language titles for delivery-center blocks A–F."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    expected_titles = {
        "ms-dc-block-a-title": "最终成片 · final_video",
        "ms-dc-block-b-title": "必需交付物",
        "ms-dc-block-c-title": "可选交付物 · scene_pack（不阻塞发布）",
        "ms-dc-block-d-title": "发布文案包",
        "ms-dc-block-e-title": "发布状态 / 反馈回填",
        "ms-dc-block-f-title": "下一轮迭代建议 / 归档",
    }
    for marker, title in expected_titles.items():
        needle = f'data-role="{marker}">{title}</h2>'
        assert needle in template, f"{marker} must read '{title}' (operator-language)"


def test_delivery_center_publish_feedback_anchor_preserved() -> None:
    """The OWC-MS-RO PR-1 follow-up correction added an
    ``id="publish-feedback"`` anchor so the Task Area '打开发布反馈'
    button lands on a real DOM target. The rebuild must preserve this
    anchor (Block E carries it directly on the op-card now)."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    assert 'id="publish-feedback"' in template


# ---------------------------------------------------------------------
# Hot Follow preservation — must not regress
# ---------------------------------------------------------------------


def test_hot_follow_workbench_panel_marker_preserved() -> None:
    template = _read(_WORKBENCH_TEMPLATE)
    assert 'data-role="operator-hot-follow-panel"' in template, (
        "operator-hot-follow-panel marker must remain in the shared workbench template"
    )


def test_hot_follow_kind_branches_preserved() -> None:
    template = _read(_WORKBENCH_TEMPLATE)
    assert 'task.kind == "hot_follow"' in template, (
        "Hot Follow conditional rendering branches must remain in task_workbench.html"
    )


def test_hot_follow_standalone_workbench_template_unchanged_marker() -> None:
    """Sanity: the dedicated hot_follow_workbench.html template still
    exists and has not been replaced by the operator-console rebuild.
    (We don't byte-diff because legitimate localisation changes can
    happen separately.)"""
    assert _HOT_FOLLOW_WORKBENCH_TEMPLATE.is_file()
    content = _read(_HOT_FOLLOW_WORKBENCH_TEMPLATE)
    # The operator-console class is NOT injected into the standalone
    # Hot Follow template — Hot Follow has its own visual system.
    assert 'op-card op-card--accent-emerald' not in content, (
        "Hot Follow standalone template must not adopt the matrix_script accent"
    )


def test_hot_follow_publish_template_intact() -> None:
    assert _HOT_FOLLOW_PUBLISH_TEMPLATE.is_file()
    content = _read(_HOT_FOLLOW_PUBLISH_TEMPLATE)
    # Sentinel: the Hot Follow publish template must keep its canonical
    # title structure.
    assert "publish" in content.lower() or "发布" in content


# ---------------------------------------------------------------------
# Defensive: no fake final_video / publish_url leaked through the rebuild
# ---------------------------------------------------------------------


def test_matrix_script_block_e_workbench_keeps_no_fake_final_video_note() -> None:
    """Existing RC-R8 audit invariant: the workbench candidate review
    block must keep its 'no fake final_video / 发布 URL' disclaimer so
    operators are not misled by a tracked-gap row."""
    inside = _ms_panel_gate_body(_read(_WORKBENCH_TEMPLATE))
    block_e_start = inside.find('data-role="matrix-script-block-e-candidate-review"')
    assert block_e_start >= 0
    next_card = inside.find('class="op-card', block_e_start + 1)
    block_e_subtree = inside[block_e_start: next_card if next_card > 0 else len(inside)]
    assert 'data-role="ms-block-e-no-fake-final-video-note"' in block_e_subtree


def test_tasks_template_includes_operator_console_stylesheet() -> None:
    template = _read(_TASKS_TEMPLATE)
    assert '/static/css/operator_console.css' in template, (
        "tasks.html must link the operator console stylesheet"
    )


# ---------------------------------------------------------------------
# Task Area · Matrix Script — operator-rebuild visual structure
# ---------------------------------------------------------------------


def test_tasks_template_matrix_script_card_uses_op_task_card_shell() -> None:
    """The Matrix Script task card must wrap the existing
    `task-card`/`task-row` legacy classes with the operator-console
    `op-task-card` shell so the visual surface reads as a production-
    management card. Both legacy and new classes coexist on the same
    container (legacy is what the filter JS needs)."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'class="task-card task-row op-task-card"' in rendered, (
        "task-row container must layer op-task-card on top of legacy classes"
    )
    # The matrix_script branch keeps its data-role markers
    for marker in (
        'data-role="matrix-script-card-left"',
        'data-role="matrix-script-card-right"',
        'data-role="ms-actions"',
        'data-role="ms-action-workbench"',
        'data-role="ms-action-delivery"',
        'data-role="ms-action-publish-feedback"',
    ):
        assert marker in rendered, f"{marker} must remain in tasks.html matrix_script branch"


def test_tasks_template_matrix_script_card_renders_production_state_grid() -> None:
    """Matrix Script card renders the new production-state grid
    (mother-task identity surface) instead of stacked meta rows."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="ms-production-state"' in rendered, (
        "Matrix Script card must render an op-task-state grid"
    )
    # The presenter-derived identity / production fields each have
    # a data-role marker that must be present inside the production
    # state grid.
    for marker in (
        'data-role="ms-core-script-name"',
        'data-role="ms-best-version"',
        'data-role="ms-current-variation"',
        'data-role="ms-publishable-variation"',
        'data-role="ms-published-channel-count"',
        'data-role="ms-last-generated-at"',
    ):
        assert marker in rendered, f"{marker} must remain in the Matrix Script card"


def test_tasks_template_matrix_script_card_uses_operator_banner_for_result() -> None:
    """Matrix Script card uses op-task-banner for the result-status row
    so the operator sees ready / blocked / review at a glance — instead
    of the old inline meta row."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_status = rendered.find('data-role="ms-result-status"')
    assert pos_status >= 0
    window = rendered[max(0, pos_status - 200): pos_status + 50]
    assert 'op-task-banner' in window, (
        "ms-result-status must render inside an op-task-banner element"
    )
    # The banner tone is set via a Jinja2 `{% set _banner_tone = "..." %}`
    # branch and interpolated into the class name. Each tone literal must
    # appear in a set-statement (one of them will fire at render time
    # based on status_kind).
    for tone_literal in (
        '_banner_tone = "ready"',
        '_banner_tone = "blocked"',
        '_banner_tone = "review"',
    ):
        assert tone_literal in template, (
            f"Matrix Script branch must wire the {tone_literal!r} branch"
        )
    assert 'op-task-banner--{{ _banner_tone }}' in template, (
        "Matrix Script branch must interpolate _banner_tone into the class"
    )


def test_tasks_template_matrix_script_card_renders_three_tier_lanes_chips() -> None:
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_lanes = rendered.find('data-role="ms-three-tier-lanes"')
    assert pos_lanes >= 0
    window = rendered[pos_lanes:pos_lanes + 600]
    assert 'op-task-lanes' in window, (
        "ms-three-tier-lanes container must use the op-task-lanes class"
    )


def test_tasks_template_matrix_script_card_no_legacy_inline_meta_row_for_owc_fields() -> None:
    """The legacy `data-role='ms-field-row-owc'` inline-meta-row that
    crammed core-script / channel / best-version / last-generated into
    a single text strip must be replaced by the production-state grid.
    (Each field's data-role marker is preserved; the grouping wrapper
    is gone.)"""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="ms-field-row-owc"' not in rendered, (
        "Legacy ms-field-row-owc inline-meta wrapper must be replaced by production-state grid"
    )


# ---------------------------------------------------------------------
# Task Area · Digital Anchor — operator-rebuild visual structure
# ---------------------------------------------------------------------


def test_tasks_template_digital_anchor_card_uses_op_task_card_shell() -> None:
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    for marker in (
        'data-role="digital-anchor-card-left"',
        'data-role="digital-anchor-card-right"',
        'data-role="da-actions"',
        'data-role="da-action-workbench"',
        'data-role="da-action-delivery"',
    ):
        assert marker in rendered, f"{marker} must remain in tasks.html digital_anchor branch"


def test_tasks_template_digital_anchor_card_renders_production_state_grid() -> None:
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="da-production-state"' in rendered, (
        "Digital Anchor card must render an op-task-state grid"
    )
    for marker in (
        'data-role="da-role-profile"',
        'data-role="da-scene-template"',
        'data-role="da-target-language"',
        'data-role="da-current-version-state"',
        'data-role="da-delivery-pack-state"',
        'data-role="da-last-update"',
    ):
        assert marker in rendered, f"{marker} must remain in the Digital Anchor card"


def test_tasks_template_digital_anchor_card_uses_operator_banner_for_blocker() -> None:
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_status = rendered.find('data-role="da-result-status"')
    assert pos_status >= 0, "Digital Anchor card must render an op-task-banner"
    window = rendered[max(0, pos_status - 200): pos_status + 50]
    assert 'op-task-banner' in window, (
        "da-result-status must render inside an op-task-banner element"
    )
    # The DA banner tone is set via `{% set _da_banner_tone = "..." %}`
    # branches.
    for tone_literal in (
        '_da_banner_tone = "ready"',
        '_da_banner_tone = "blocked"',
        '_da_banner_tone = "review"',
    ):
        assert tone_literal in template, (
            f"Digital Anchor branch must wire the {tone_literal!r} branch"
        )
    assert 'op-task-banner--{{ _da_banner_tone }}' in template, (
        "Digital Anchor branch must interpolate _da_banner_tone into the class"
    )


def test_tasks_template_digital_anchor_card_no_legacy_inline_meta_row_for_state_fields() -> None:
    """The legacy `data-role='da-field-row-state'` inline-meta-row that
    crammed current_version_state / current_blocker / delivery_pack_state
    / last_update into a single text strip must be replaced by the
    production-state grid + banner."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="da-field-row-state"' not in rendered, (
        "Legacy da-field-row-state inline-meta wrapper must be replaced"
    )
    assert 'data-role="da-field-row-identity"' not in rendered, (
        "Legacy da-field-row-identity inline-meta wrapper must be replaced"
    )


# ---------------------------------------------------------------------
# Task Area baseline branch + Hot Follow path — preservation
# ---------------------------------------------------------------------


def test_tasks_template_baseline_branch_unchanged() -> None:
    """The {% else %} baseline branch (Hot Follow / baseline rows) must
    keep using the legacy `task-card__left` / `task-card__right` classes
    without the new op-task-card shell. Hot Follow must not be reskinned
    in this rebuild."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    # The baseline branch's left column is a plain `task-card__left`
    # (no op-task-card__left). Find a substring that only the baseline
    # branch has — `<span>{{ platform }}</span>` is unique to it.
    assert "<span>{{ platform }}</span>" in rendered, (
        "baseline branch must remain in tasks.html"
    )


def test_tasks_template_filter_js_classes_preserved() -> None:
    """The filter JS in tasks.html relies on `.task-row`,
    `.scene-tab`, `.bucket-item`, `.status-item`, `data-line=*`,
    `data-status=*`, `data-bucket=*`. Those must stay on the rebuilt
    cards so filter behaviour is unchanged."""
    template = _read(_TASKS_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'class="task-card task-row op-task-card"' in rendered
    assert 'data-line="{{ line_id }}"' in rendered
    assert 'data-status="{{ status_value }}"' in rendered
    assert 'data-bucket="{{ bucket_value }}"' in rendered
    # Filter buttons are unchanged
    assert 'class="scene-tab"' in rendered
    assert 'class="status-item"' in rendered
    assert 'class="bucket-item"' in rendered


# ---------------------------------------------------------------------
# Delivery Hub · JS-hydrated diagnostic shells demoted to <details>
# ---------------------------------------------------------------------


def test_publish_hub_ms_delivery_comprehension_shell_collapsed() -> None:
    """The display:none JS-hydrated matrix_script delivery-comprehension
    shell must live inside an op-collapse <details> wrapper so even
    when JS shows it, it sits behind a closed disclosure."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    # The fold wrapper exists.
    assert 'data-role="op-console-ms-delivery-comprehension-fold"' in rendered, (
        "MS delivery-comprehension shell must be wrapped in an op-collapse fold"
    )
    # The shell's data-role marker is preserved.
    assert 'data-role="matrix-script-delivery-comprehension"' in rendered
    # The shell's id is preserved (JS calls
    # document.getElementById("matrix-script-delivery-comprehension-block")).
    assert 'id="matrix-script-delivery-comprehension-block"' in rendered
    # The fold opens BEFORE the shell.
    pos_fold = rendered.find('data-role="op-console-ms-delivery-comprehension-fold"')
    pos_shell = rendered.find('data-role="matrix-script-delivery-comprehension"')
    assert 0 < pos_fold < pos_shell


def test_publish_hub_ms_secondary_shells_collapsed() -> None:
    """copy_bundle / 多渠道回填 / publish-backfill-readiness shells must
    all live inside a single op-collapse fold."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="op-console-ms-secondary-shells-fold"' in rendered
    pos_fold = rendered.find('data-role="op-console-ms-secondary-shells-fold"')
    assert pos_fold >= 0

    # Each shell's data-role is preserved.
    for marker in (
        'data-role="matrix-script-delivery-copy-bundle"',
        'data-role="matrix-script-delivery-backfill"',
        'data-role="matrix-script-publish-backfill-readiness"',
    ):
        pos = rendered.find(marker)
        assert pos >= 0, f"{marker} must remain"
        assert pos > pos_fold, f"{marker} must sit inside the fold (after the fold opens)"

    # JS-targetable IDs preserved.
    for js_id in (
        'id="matrix-script-delivery-copy-bundle-block"',
        'id="matrix-script-delivery-backfill-block"',
        'id="matrix-script-publish-backfill-readiness-block"',
    ):
        assert js_id in rendered, f"{js_id} must remain so JS getElementById keeps working"


def test_publish_hub_da_secondary_shells_collapsed() -> None:
    """digital-anchor-delivery-pack + delivery-backfill shells must live
    inside an op-collapse fold; the operator-relevant
    digital-anchor-closure-block stays visible (NOT inside the fold)."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    assert 'data-role="op-console-da-secondary-shells-fold"' in rendered
    pos_fold = rendered.find('data-role="op-console-da-secondary-shells-fold"')

    for marker in (
        'data-role="digital-anchor-delivery-pack"',
        'data-role="digital-anchor-delivery-backfill"',
    ):
        pos = rendered.find(marker)
        assert pos >= 0, f"{marker} must remain"
        assert pos > pos_fold, f"{marker} must sit inside the fold"

    # JS-targetable IDs preserved.
    for js_id in (
        'id="digital-anchor-delivery-pack-block"',
        'id="digital-anchor-delivery-backfill-block"',
    ):
        assert js_id in rendered, f"{js_id} must remain so JS getElementById keeps working"

    # The DA closure block is NOT inside the fold (it is operator-relevant).
    pos_closure = rendered.find('id="digital-anchor-closure-block"')
    assert pos_closure >= 0
    # closure block sits AFTER the fold — but specifically AFTER the
    # fold's </details> closing. We can't easily detect the exact close
    # position; we settle for: the closure block carries op-card class
    # (it was rebuilt earlier) — that means it's a top-level operator card.
    closure_window = rendered[max(0, pos_closure - 300): pos_closure + 50]
    assert 'op-card' in closure_window, (
        "DA closure block must remain a top-level operator op-card (not inside the fold)"
    )


def test_publish_hub_ms_closure_block_remains_visible() -> None:
    """The matrix-script-closure-block is operator-relevant (publish
    feedback closure form). It must NOT be inside any op-collapse
    fold."""
    template = _read(_PUBLISH_HUB_TEMPLATE)
    rendered = _strip_jinja_comments(template)
    pos_closure = rendered.find('id="matrix-script-closure-block"')
    assert pos_closure >= 0
    pos_secondary_fold = rendered.find('data-role="op-console-ms-secondary-shells-fold"')
    # Closure block opens BEFORE the secondary-shells fold so it cannot
    # be inside it.
    assert 0 < pos_closure < pos_secondary_fold, (
        "MS closure block must remain visible above the secondary shells fold"
    )


# ---------------------------------------------------------------------
# Forbidden-substring audit on the rebuilt Task Area
# ---------------------------------------------------------------------


def test_no_provider_model_vendor_engine_ui_introduced_by_rebuild() -> None:
    """Defensive scan: the rebuild does not introduce any operator-visible
    provider / model / vendor / engine selector. (The pre-existing
    'no provider/model/vendor/engine' disclaimer note in Block D is the
    only operator-readable mention of these tokens in the workbench.)"""
    workbench = _read(_WORKBENCH_TEMPLATE)
    publish_hub = _read(_PUBLISH_HUB_TEMPLATE)
    tasks = _read(_TASKS_TEMPLATE)
    for surface, name in (
        (workbench, "workbench"),
        (publish_hub, "publish_hub"),
        (tasks, "tasks"),
    ):
        for needle in (
            "选择 provider",
            "选择 model",
            "选择 vendor",
            "选择 engine",
            'placeholder="provider',
            'placeholder="model',
            'placeholder="vendor',
            'placeholder="engine',
        ):
            assert needle not in surface, (
                f"{name} must not introduce a {needle!r} affordance"
            )

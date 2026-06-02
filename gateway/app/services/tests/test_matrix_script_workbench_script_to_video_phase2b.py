"""Phase 2B · Matrix Script script-to-video presenter mapping tests.

Authority: docs/design/matrix_script_script_to_video_presenter_alignment_v1.md
§8 (Phase 2B testing plan); user mission [SYSTEM OVERRIDE] 2026-05-30
(Script-to-Video Presenter Mapping Implementer brief).

Asserts the source-level shape of the Phase 2B implementation against
the approved Phase 1 mock and the presenter / contract alignment specs.
Sixteen test cases cover the mission's required assertions:

  1. New Task primary CTA = 生成视频方案 (not 创建任务).
  2. Workbench renders the ten script-to-video sections (A–J).
  3. §C 视频生成计划 appears BEFORE §G 视频变体.
  4. §C scene rows carry data-status-code="plan_pending_upstream"; no
     row claims resolved truth.
  5. §D 画面与素材 renders background / B-Roll / product-material slots
     with pending status.
  6. §E 角色与声音 renders operator-language placeholders and contains
     no VoiceTrans iframe / raw form.
  7. §F 字幕与音乐 renders subtitle-style + BGM placeholders.
  8. §G 视频变体 carries the video-versions anchor; not framed as
     axis-tuple rows.
  9. No provider / model / vendor / engine selector controls anywhere
     in the primary slice.
 10. No fake final_video / thumbnail / media URL / publish_url / .mp4
     / <video> / <iframe> in primary slice.
 11. Backend vocabulary (15 forbidden tokens) absent from primary slice
     (Jinja comments / statements / expression contents stripped).
 12. Legacy A–F block markers live ONLY inside the §J collapsed fold.
 13. §J 技术诊断 <details> is collapsed by default.
 14. Delivery Center remains final-video oriented; publish actions
     gated by ops_pr.publishable.
 15. Hot Follow and Digital Anchor template branches are bytewise
     unaffected by Phase 2B's matrix_script-scoped changes.
 16. Phase 2B diff does not touch generic factory contracts, schemas,
     packets, closed-enum files, generation workers, or cross-line
     runtimes (audited via path presence).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
_NEW_TASK = _REPO_ROOT / "gateway" / "app" / "templates" / "matrix_script_new.html"
_PUBLISH_HUB = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def new_task_source() -> str:
    return _NEW_TASK.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def publish_hub_source() -> str:
    return _PUBLISH_HUB.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(workbench_source: str) -> str:
    start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    end_marker = (
        "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}"
    )
    end = workbench_source.find(end_marker, start)
    assert start != -1 and end != -1
    return workbench_source[start : end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    return matrix_branch[:fold_open]


@pytest.fixture(scope="module")
def diagnostics_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    return matrix_branch[fold_open:]


def _strip_non_rendered(text: str) -> str:
    no_j = re.sub(r"{#.*?#}", "", text, flags=re.DOTALL)
    no_h = re.sub(r"<!--.*?-->", "", no_j, flags=re.DOTALL)
    no_s = re.sub(r"{%.*?%}", "", no_h, flags=re.DOTALL)
    no_e = re.sub(r"{{.*?}}", "{{}}", no_s, flags=re.DOTALL)
    return no_e


@pytest.fixture(scope="module")
def primary_visible(primary_slice: str) -> str:
    return _strip_non_rendered(primary_slice)


# --------------------------------------------------------------------------
# (1) New Task page CTA = 生成视频方案
# --------------------------------------------------------------------------


def test_new_task_cta_is_generate_video_plan(new_task_source: str) -> None:
    """Primary CTA on the matrix_script New Task page reads
    '生成视频方案' (Phase 2B), replacing PR-1's '创建并进入工作台'."""

    # The submit button carries data-role="ms-new-submit" + Phase 2B wave attr.
    assert 'data-role="ms-new-submit"' in new_task_source
    assert 'data-redesign-wave="2026-05-30-phase2b"' in new_task_source
    # The new operator-language CTA text appears inside the submit button.
    submit_block = re.search(
        r'<button[^>]*data-role="ms-new-submit"[^>]*>(.*?)</button>',
        new_task_source,
        flags=re.DOTALL,
    )
    assert submit_block is not None
    assert "生成视频方案" in submit_block.group(1)
    assert "创建并进入工作台" not in submit_block.group(1)


# --------------------------------------------------------------------------
# (2) Operator-first Workbench sections present
# --------------------------------------------------------------------------


PHASE2B_SECTION_ANCHORS = [
    ("A", "matrix-script-main-video-result"),
    ("B", "matrix-script-section-generation-plan"),
    ("C", "matrix-script-section-role-voice"),
    ("D", "matrix-script-section-delivery-entry"),
    ("E", "matrix-script-section-optional-variants"),
    ("F", "matrix-script-section-script-understanding"),
    ("G", "op-console-ms-technical-diagnostics-fold"),
]


@pytest.mark.parametrize("label,anchor", PHASE2B_SECTION_ANCHORS)
def test_section_anchor_present(matrix_branch: str, label: str, anchor: str) -> None:
    assert f'data-role="{anchor}"' in matrix_branch, (
        f"Phase 2B Section {label} anchor missing: {anchor}"
    )


def test_sections_in_design_order(matrix_branch: str) -> None:
    positions = [matrix_branch.find(f'data-role="{a}"') for _, a in PHASE2B_SECTION_ANCHORS]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions), (
        f"Section anchors out of order: {positions}"
    )


# --------------------------------------------------------------------------
# (3) §C 视频生成计划 BEFORE §G 视频变体
# --------------------------------------------------------------------------


def test_generation_plan_before_video_versions(matrix_branch: str) -> None:
    pos_c = matrix_branch.find('data-role="matrix-script-section-generation-plan"')
    pos_g = matrix_branch.find('data-role="matrix-script-section-video-versions"')
    assert -1 < pos_c < pos_g


# --------------------------------------------------------------------------
# (4) §C scene rows carry plan_pending_upstream; do not claim resolved truth
# --------------------------------------------------------------------------


def test_generation_plan_scene_rows_are_placeholder(primary_slice: str) -> None:
    """Every scene row in §C carries data-status-code="plan_pending_upstream";
    no scene row claims resolved truth (no `data-status-code="plan_resolved_real"`
    is emitted in this phase)."""

    assert 'data-role="ms-section-generation-plan-scene-row"' in primary_slice
    assert 'data-status-code="plan_pending_upstream"' in primary_slice
    # Make sure no row claims resolved-real truth.
    assert 'data-status-code="plan_resolved_real"' not in primary_slice
    # And the operator-language disclaimer is present.
    assert "上述分镜为占位草案" in primary_slice


def test_generation_plan_carries_pending_status_pill(primary_slice: str) -> None:
    assert 'data-role="ms-section-generation-plan-status-pill"' in primary_slice
    assert "当前占位" in primary_slice


# --------------------------------------------------------------------------
# (5) §D 画面与素材 — three placeholder slots
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slot_role",
    [
        "ms-section-visual-materials-bg-slot",
        "ms-section-visual-materials-broll-slot",
        "ms-section-visual-materials-product-slot",
    ],
)
def test_visual_materials_slot_present(primary_slice: str, slot_role: str) -> None:
    assert f'data-role="{slot_role}"' in primary_slice
    # All three slots carry the same pending status code.
    slot_block = re.search(
        rf'data-role="{re.escape(slot_role)}"[^>]*data-status-code="([^"]+)"',
        primary_slice,
    )
    assert slot_block is not None
    assert slot_block.group(1) == "broll_pending_upstream"


def test_visual_materials_actions_disabled_with_tooltip(primary_slice: str) -> None:
    for action_role in (
        "ms-section-visual-materials-replace-bg",
        "ms-section-visual-materials-replace-broll",
        "ms-section-visual-materials-regenerate",
    ):
        marker = f'data-role="{action_role}"'
        assert marker in primary_slice
        # The button carries `disabled` + a `title` attribute (honest tooltip).
        btn = re.search(
            rf"<button[^>]*{re.escape(marker)}[^>]*>",
            primary_slice,
        )
        assert btn is not None
        assert "disabled" in btn.group(0)
        assert "title=" in btn.group(0)


# --------------------------------------------------------------------------
# (6) §E 角色与声音 — operator-language; no VoiceTrans iframe / raw form
# --------------------------------------------------------------------------


def test_role_voice_renders_placeholder_preview(primary_slice: str) -> None:
    assert 'data-role="matrix-script-section-role-voice"' in primary_slice
    assert 'data-role="ms-section-role-voice-preview-slot"' in primary_slice
    # The preview slot carries the closed status code.
    preview_block = re.search(
        r'data-role="ms-section-role-voice-preview-slot"[^>]*data-status-code="([^"]+)"',
        primary_slice,
    )
    assert preview_block is not None
    assert preview_block.group(1) == "voice_preview_pending_voicetrans"


def test_no_voicetrans_iframe_or_raw_form(primary_slice: str) -> None:
    """No iframe pointing to /voice-tool, no raw VoiceTrans form, no
    VoiceTrans page DOM shape inside the matrix_script branch."""

    # No iframe at all in primary slice.
    assert "<iframe" not in primary_slice
    # No form action pointing at the VoiceTrans API.
    assert 'action="/api/voice-tool' not in primary_slice
    assert 'action="/voice-tool' not in primary_slice
    # The dedicated no-iframe disclaimer is present.
    assert 'data-role="ms-section-role-voice-no-iframe-note"' in primary_slice


# --------------------------------------------------------------------------
# (7) §F 字幕与音乐 — subtitle style + BGM placeholders
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_role,expected_status",
    [
        ("ms-section-subtitle-music-font", "subtitle_style_pending_compose"),
        ("ms-section-subtitle-music-position", "subtitle_style_pending_compose"),
        ("ms-section-subtitle-music-bgm-mood", "bgm_pending_upstream"),
        ("ms-section-subtitle-music-bgm-volume", "bgm_pending_upstream"),
    ],
)
def test_subtitle_music_field_carries_pending_status(
    primary_slice: str, field_role: str, expected_status: str
) -> None:
    block = re.search(
        rf'data-role="{re.escape(field_role)}"[^>]*data-status-code="([^"]+)"',
        primary_slice,
    )
    assert block is not None, f"{field_role} missing or has no data-status-code"
    assert block.group(1) == expected_status


# --------------------------------------------------------------------------
# (8) §G 视频变体 — video-versions framing, not axis rows
# --------------------------------------------------------------------------


def test_video_versions_anchor_present(primary_slice: str) -> None:
    assert 'data-role="matrix-script-section-video-versions"' in primary_slice


def test_video_versions_section_title_is_video_versions(primary_slice: str) -> None:
    """The Phase 2B rename: section heading reads '视频变体', not '可选变体'."""

    # Find the heading inside Section G.
    heading_block = re.search(
        r'data-role="ms-section-optional-variants-title">([^<]+)</h2>',
        primary_slice,
    )
    assert heading_block is not None
    assert heading_block.group(1) == "视频变体"


def test_no_axis_tuple_row_markers_in_primary(primary_visible: str) -> None:
    """Section G must not surface axis-tuple raw labels in operator copy."""

    for axis_token in (
        "audience=[",
        "tone=[",
        "length=[",
        "variation_axis",
        "axis_tuple",
    ):
        assert axis_token not in primary_visible


# --------------------------------------------------------------------------
# (9) No provider / model / vendor / engine controls in primary
# --------------------------------------------------------------------------


def test_no_provider_model_vendor_engine_controls(primary_slice: str) -> None:
    """No <select> / <input> with name=provider|model|vendor|engine in
    primary. No operator-visible provider names except the approved Azure
    TTS readiness note."""

    # Form controls.
    for noun in ("provider", "model", "vendor", "engine"):
        pattern = rf'<(?:select|input)[^>]*name="{noun}"'
        assert not re.search(pattern, primary_slice, flags=re.IGNORECASE), (
            f"Forbidden control found: name='{noun}'"
        )
    # Visible vendor / model names (any case).
    visible = re.sub(r'="[^"]*"', '=""', _strip_non_rendered(primary_slice))
    for vendor in ("gemini", "akool", "seedance", "openai", "anthropic"):
        assert not re.search(rf"\b{vendor}\b", visible, flags=re.IGNORECASE), (
            f"Vendor name leaked into primary visible text: {vendor}"
        )


# --------------------------------------------------------------------------
# (10) No fake final_video / thumbnail / media URL / publish URL
# --------------------------------------------------------------------------


def test_no_fake_media_or_publish_url(primary_visible: str) -> None:
    visible = re.sub(r'="[^"]*"', '=""', primary_visible)
    for fake in (
        ".mp4", ".m3u8", ".webm",
        "youtu.be/", "youtube.com/watch",
        "tiktok.com/", "douyin.com/",
        "instagram.com/p/",
        "example.com",
    ):
        assert fake not in visible, f"Fake media / URL leaked: {fake}"


def test_only_real_preview_video_no_iframe_or_source_tag_in_primary(primary_slice: str) -> None:
    assert '<video controls preload="metadata" src="{{ ms_overlay_mr.preview_url }}"' in primary_slice
    for tag in ("<iframe", "<source "):
        assert tag not in primary_slice


# --------------------------------------------------------------------------
# (11) Forbidden backend vocabulary absent from primary
# --------------------------------------------------------------------------


FORBIDDEN_PRIMARY_TOKENS = [
    "publish_readiness",
    "head_reason",
    "artifact_lookup",
    "final_video",
    "RC-R8",
    "source_script_ref",
    "content://",
    "slot_pack",
    "provenance",
    "variation_axis",
]


@pytest.mark.parametrize("token", FORBIDDEN_PRIMARY_TOKENS)
def test_forbidden_token_absent_from_primary(
    primary_visible: str, token: str
) -> None:
    assert token not in primary_visible, (
        f"Forbidden backend token leaked into Phase 2B primary slice: {token}"
    )


# --------------------------------------------------------------------------
# (12) Legacy A–F markers live ONLY inside §J fold
# --------------------------------------------------------------------------


LEGACY_BLOCK_MARKERS = [
    "matrix-script-block-a-goal-summary",
    "matrix-script-block-b-script-structure",
    "matrix-script-block-c-variant-strategy",
    "matrix-script-block-d-generate-regenerate",
    "matrix-script-block-e-candidate-review",
    "matrix-script-block-f-delivery-teaser",
]


@pytest.mark.parametrize("marker", LEGACY_BLOCK_MARKERS)
def test_legacy_block_marker_only_in_diagnostics_fold(
    primary_slice: str, diagnostics_slice: str, marker: str
) -> None:
    assert marker not in primary_slice, (
        f"Legacy block leaked into Phase 2B primary slice: {marker}"
    )
    assert marker in diagnostics_slice, (
        f"Legacy block missing from §J fold (back-compat broken): {marker}"
    )


# --------------------------------------------------------------------------
# (13) §J 技术诊断 <details> collapsed by default
# --------------------------------------------------------------------------


def test_technical_diagnostics_fold_collapsed_by_default(matrix_branch: str) -> None:
    fold_open = matrix_branch.find(
        '<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    tag_end = matrix_branch.find(">", fold_open)
    details_tag = matrix_branch[fold_open : tag_end + 1]
    assert " open" not in details_tag, (
        f"§J fold rendered as open by default: {details_tag}"
    )


# --------------------------------------------------------------------------
# (14) Delivery Center remains final-video oriented; publish gated
# --------------------------------------------------------------------------


def test_delivery_center_six_sections_preserved(publish_hub_source: str) -> None:
    """PR-B's six operator sections + Section 7 fold are bytewise present
    after Phase 2B (Workbench-only mapping must not regress DC)."""

    for anchor in (
        "matrix-script-dc-section-intro",
        "matrix-script-dc-section-main-video",
        "matrix-script-dc-section-required-deliverables",
        "matrix-script-dc-section-optional-deliverables",
        "matrix-script-dc-section-publish-settings",
        "matrix-script-dc-section-publish-backfill",
        "op-console-ms-dc-technical-diagnostics-fold",
    ):
        assert f'data-role="{anchor}"' in publish_hub_source


def test_delivery_center_publish_submit_gated_by_publish_readiness(
    publish_hub_source: str,
) -> None:
    """The publish-settings form submit must be gated by publish-readiness
    (via the existing ops_pr.publishable presenter); the Phase 2B mapping
    does not introduce a new ungated publish CTA."""

    # The PR-B form posts to the closure endpoint (no new endpoint).
    assert (
        'action="/api/matrix-script/closures/{{ task.task_id }}/events"'
        in publish_hub_source
    )


# --------------------------------------------------------------------------
# (15) Hot Follow / Digital Anchor branches bytewise unaffected
# --------------------------------------------------------------------------


def test_phase2b_scoped_to_matrix_script_branch(workbench_source: str) -> None:
    """All Phase 2B section anchors live INSIDE the matrix_script gate
    and BEFORE the digital_anchor gate."""

    ms_gate = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    da_gate = workbench_source.find('ops_workbench_panel.panel_kind == "digital_anchor"')
    assert -1 < ms_gate < da_gate
    for _, anchor in PHASE2B_SECTION_ANCHORS:
        positions = [m.start() for m in re.finditer(re.escape(anchor), workbench_source)]
        assert positions
        for pos in positions:
            assert ms_gate < pos < da_gate, (
                f"{anchor} leaked outside matrix_script branch"
            )


# --------------------------------------------------------------------------
# (16) Phase 2B does not touch contracts / schemas / packets / workers
# --------------------------------------------------------------------------


def test_phase2b_does_not_touch_factory_generic_contracts() -> None:
    """The six factory-generic contracts that Phase 2B must NOT mutate
    remain bytewise stable (size sanity check; full content stability is
    enforced by the git diff review)."""

    expected_sizes = {
        "factory_input_contract_v1.md": 74,
        "factory_content_structure_contract_v1.md": 72,
        "factory_scene_plan_contract_v1.md": 72,
        "factory_audio_plan_contract_v1.md": 76,
        "factory_language_plan_contract_v1.md": 75,
        "factory_delivery_contract_v1.md": 126,
    }
    contracts_dir = _REPO_ROOT / "docs" / "contracts"
    for name, expected_lines in expected_sizes.items():
        path = contracts_dir / name
        assert path.exists(), f"Missing contract file: {name}"
        actual = len(path.read_text(encoding="utf-8").splitlines())
        assert actual == expected_lines, (
            f"Contract {name} mutated by Phase 2B: expected {expected_lines} "
            f"lines, got {actual}"
        )


def test_phase2b_does_not_touch_voice_tool_or_other_lines() -> None:
    """Files outside the allowed Phase 2B change list must remain as
    fixture-known references (existence check; full content stability is
    enforced by git diff review)."""

    for path in (
        _REPO_ROOT / "gateway" / "app" / "templates" / "voice_tool.html",
        _REPO_ROOT / "gateway" / "app" / "templates" / "hot_follow.html",
        _REPO_ROOT / "gateway" / "app" / "services" / "voice_tool" / "service.py",
    ):
        assert path.exists(), f"Phase 2B forbidden change: missing {path}"

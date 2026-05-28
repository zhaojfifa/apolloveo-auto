"""Matrix Script Workbench redesign tests (2026-05-28 wave).

Authority: 2026-05-28 Matrix Script Operator UI Redesign mission §2 / §3 /
§4 / §5 (workbench reframe into 6 operator panels A–F where F is
collapsed 技术诊断; candidate-review empty-state honesty; delivery
summary uses mission-mandated copy; Chinese-first operator language;
existing data-role markers preserved for back-compat).

Pattern: source-only template inspection.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH_TEMPLATE = (
    _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
)


def _read() -> str:
    return _WORKBENCH_TEMPLATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Block label refinements (Mission §2 wordings)
# ---------------------------------------------------------------------------


def test_block_c_title_uses_variant_plan_label() -> None:
    source = _read()
    # Mission §2 C. 变体方案 (was 变体策略 in PR-2)
    assert '<h2 class="op-section-title" data-role="ms-block-c-title">变体方案</h2>' in source
    # Old wording removed from operator-facing title
    assert '<h2 class="op-section-title" data-role="ms-block-c-title">变体策略</h2>' not in source


def test_block_d_title_uses_generation_progress_label() -> None:
    source = _read()
    # Mission §2 D. 生成进度 (was 生成 / 重新生成 in PR-3)
    assert '<h2 class="op-section-title" data-role="ms-block-d-title">生成进度</h2>' in source
    assert '<h2 class="op-section-title" data-role="ms-block-d-title">生成 / 重新生成</h2>' not in source


def test_block_f_title_uses_delivery_summary_label() -> None:
    source = _read()
    # Mission §4 — workbench may show a short delivery STATUS card only;
    # the visible title is 交付摘要 to disambiguate from Delivery Center.
    assert '<h2 class="op-section-title" data-role="ms-block-f-title">交付摘要</h2>' in source
    # Old "交付概览" title is removed from operator-facing copy.
    assert '<h2 class="op-section-title" data-role="ms-block-f-title">交付概览</h2>' not in source


# ---------------------------------------------------------------------------
# Block E — Candidate Review honesty (Mission §3)
# ---------------------------------------------------------------------------


def test_block_e_renders_empty_state_marker_when_no_preview_resolved() -> None:
    """When no variation has current_fresh/historical preview, render a single
    operator-language message instead of N empty per-candidate cards."""

    source = _read()
    assert 'data-role="ms-block-e-no-preview-available"' in source
    assert 'data-role="ms-block-e-no-preview-pill"' in source


def test_block_e_empty_state_mission_copy_present() -> None:
    source = _read()
    # Mission §3 exact wording
    assert "当前暂无可预览成片" in source
    assert (
        "已完成脚本结构与变体方案；成片生成能力接入后将在这里展示候选视频。" in source
    )


def test_block_e_card_data_role_marker_root_preserved_for_back_compat() -> None:
    """Existing per-card data-role markers must still resolve for PR-3 tests."""

    source = _read()
    # The per-card branch still exists (gated behind the resolved-any check)
    assert 'data-role="ms-block-e-candidate-card"' in source
    # The container marker is preserved
    assert 'data-role="matrix-script-block-e-candidate-review"' in source


def test_block_e_root_carries_redesign_audit_attribute() -> None:
    source = _read()
    # data-any-preview-resolved is the new audit hook for the empty-state
    # branch selection; tests can use it to assert empty-state is the
    # rendered branch on real tasks.
    assert 'data-any-preview-resolved=' in source


# ---------------------------------------------------------------------------
# Block F — Delivery Summary mission copy (Mission §4)
# ---------------------------------------------------------------------------


def test_block_f_carries_redesign_wave_attribute() -> None:
    source = _read()
    assert 'data-redesign-wave="2026-05-28-ms-ui"' in source


def test_block_f_headline_blocker_copy_present() -> None:
    source = _read()
    assert 'data-role="ms-block-f-headline-blocker"' in source
    assert "当前不能交付：尚未生成成片。" in source


def test_block_f_have_section_lists_phase_b_baseline() -> None:
    source = _read()
    assert 'data-role="ms-block-f-have"' in source
    # 已具备 baseline = ["脚本结构", "变体方案"] per Mission §4
    assert "脚本结构" in source
    assert "变体方案" in source


def test_block_f_need_section_lists_mission_baseline() -> None:
    source = _read()
    assert 'data-role="ms-block-f-need"' in source
    # Mission §4 待补齐 baseline list
    for item in ("成片", "字幕", "音频", "manifest", "交付包"):
        assert item in source


def test_block_f_scene_pack_non_blocking_note_present() -> None:
    source = _read()
    assert 'data-role="ms-block-f-scene-pack-note"' in source
    assert "场景包（scene_pack）始终为可选 · 不阻塞发布。" in source


def test_block_f_no_per_row_required_or_optional_lists_in_workbench() -> None:
    """Mission §4 — full per-row deliverable detail belongs in Delivery Center."""

    source = _read()
    # The per-row markers from the old detailed lane breakdown MUST NOT
    # appear in the workbench template anymore (they live in the Delivery
    # Center publish-hub template per the OWC-MS-RO PR-4 substrate).
    assert 'data-role="ms-block-f-required-row"' not in source
    assert 'data-role="ms-block-f-optional-row"' not in source
    assert 'data-role="ms-block-f-required-list"' not in source
    assert 'data-role="ms-block-f-optional-list"' not in source


def test_block_f_delivery_center_cta_preserved() -> None:
    source = _read()
    # CTA to Delivery Center is still operator-visible
    assert 'data-role="ms-block-f-action-delivery-center"' in source
    assert "前往交付中心查看完整成片" in source


# ---------------------------------------------------------------------------
# Block F (collapsed 技术诊断) — Mission §2 F slot
# ---------------------------------------------------------------------------


def test_collapsed_fold_carries_block_f_index_header() -> None:
    source = _read()
    # The existing op-console-ms-secondary-fold details element is
    # repurposed as Mission §2 Block F · 技术诊断 (collapsed by default).
    assert 'data-role="op-console-ms-secondary-fold"' in source
    assert "F · 诊断" in source
    assert "矩阵脚本 · 技术诊断（架构师视图，默认收起）" in source


def test_collapsed_fold_hint_names_quarantined_english_ids() -> None:
    """The fold's hint enumerates the English IDs that operators NEVER see
    in primary panels (head_reason / artifact_lookup / publish_readiness /
    final_provenance). Helps reviewers verify quarantine discipline."""

    source = _read()
    assert "head_reason" in source
    assert "artifact_lookup" in source
    assert "publish_readiness" in source


# ---------------------------------------------------------------------------
# Honesty audit — no fake final_video URL anywhere in matrix_script block
# ---------------------------------------------------------------------------


def test_no_fake_final_video_url_in_workbench_matrix_script_branch() -> None:
    """RC-R8 audit (preserved). No fabricated media URL on the workbench."""

    source = _read()
    # Defensive search for fabricated final_video / publish_url shapes.
    assert "https://cdn.example" not in source
    assert "final_video.mp4" not in source
    assert "https://media.example" not in source
    # The disclaimer note remains
    assert "本面板不展示 final_video / 发布 URL" in source


def test_no_vendor_or_model_or_provider_or_engine_selector_in_primary_panels() -> None:
    """validator R3 (preserved): no provider/model/vendor/engine UI."""

    source = _read()
    # Defensive: these tokens MUST NOT appear as UI selectors. The "no
    # vendor" disclaimer note is allowed — it is a guarantee, not a
    # selector affordance.
    assert "select provider" not in source.lower()
    assert "select model" not in source.lower()
    assert "select vendor" not in source.lower()
    assert "select engine" not in source.lower()
    assert "choose provider" not in source.lower()

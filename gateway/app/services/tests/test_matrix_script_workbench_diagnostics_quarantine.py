"""Tests for PR-2D · Workbench engineering-vocabulary quarantine.

Authority: visual validation report 2026-05-28 top-5 issues #1, #2, #3.
Mission §B.4 (Workbench delivery summary stays light; full per-row
detail in Delivery Center; English IDs only in F · 诊断 fold).

This wave's surface-level guarantees:
- `publish_readiness`, `head_reason`, `final_video`, `RC-R8`,
  `artifact_lookup`, `slot_pack`, `Workbench E` MUST NOT appear in the
  operator-facing helper outputs (recommended_action_view,
  publish_backfill_readiness_view, main_video_result_view), only inside
  the architect-only F · 诊断 fold's strings.
- Block F "待补齐" MUST render the mission-mandated operator-language
  baseline ["成片", "字幕", "音频", "manifest", "交付包"], never the
  raw contract `kind_label_zh` ("变体清单 / 脚本 slot 包").
"""
from __future__ import annotations

from pathlib import Path

from gateway.app.services.matrix_script.recommended_action_view import (
    NEXT_ACTION_BLOCKED_ZH,
    NEXT_ACTION_PUBLISHABLE_ZH,
    NEXT_ACTION_UNDETERMINED_ZH,
)
from gateway.app.services.matrix_script.publish_backfill_readiness_view import (
    READINESS_ALREADY_FAILED,
    READINESS_ALREADY_PUBLISHED,
    READINESS_GATED,
    READINESS_NEXT_INPUT_ZH,
    READINESS_PUBLISHABLE_NOW,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helper string quarantine (engineering IDs gone from operator outputs)
# ---------------------------------------------------------------------------


def test_recommended_action_blocked_next_action_uses_operator_language() -> None:
    """recommended_action_view.NEXT_ACTION_BLOCKED_ZH MUST NOT carry
    `publish_readiness` or `head_reason` (Visual Issue #1)."""

    assert "publish_readiness" not in NEXT_ACTION_BLOCKED_ZH
    assert "head_reason" not in NEXT_ACTION_BLOCKED_ZH
    # The operator-language replacement names "发布门禁" + "主视频结果"
    assert "发布门禁" in NEXT_ACTION_BLOCKED_ZH
    assert "主视频结果" in NEXT_ACTION_BLOCKED_ZH


def test_recommended_action_undetermined_next_action_uses_operator_language() -> None:
    assert "publish_readiness" not in NEXT_ACTION_UNDETERMINED_ZH
    assert "发布条件" in NEXT_ACTION_UNDETERMINED_ZH


def test_publishable_next_action_unchanged() -> None:
    """The publishable narrative was operator-language already; PR-2D
    does not touch it. Pin this so a future rewrite cannot accidentally
    re-introduce engineering vocab."""

    assert "publish_readiness" not in NEXT_ACTION_PUBLISHABLE_ZH
    assert "head_reason" not in NEXT_ACTION_PUBLISHABLE_ZH


def test_publish_backfill_narratives_use_operator_language() -> None:
    """READINESS_NEXT_INPUT_ZH carries the operator-facing per-row
    narratives; engineering IDs MUST NOT appear in any of them."""

    for kind in (
        READINESS_PUBLISHABLE_NOW,
        READINESS_GATED,
        READINESS_ALREADY_PUBLISHED,
        READINESS_ALREADY_FAILED,
    ):
        narrative = READINESS_NEXT_INPUT_ZH[kind]
        for forbidden in (
            "publish_readiness",
            "head_reason",
            "delivery_comprehension",
            "final_video",
            "publish_url",
            "closure ",
            "variation ",
        ):
            assert forbidden not in narrative, (
                f"{kind!r} narrative leaks {forbidden!r}: {narrative!r}"
            )
    # The gated narrative names operator-language equivalents
    assert "发布门禁" in READINESS_NEXT_INPUT_ZH[READINESS_GATED]
    assert "主视频结果" in READINESS_NEXT_INPUT_ZH[READINESS_GATED]


# ---------------------------------------------------------------------------
# Template-level quarantine for Block D subtitle (Visual Issue #1)
# ---------------------------------------------------------------------------


def test_block_d_subtitle_no_longer_leaks_publish_readiness() -> None:
    source = _read()
    # PR-2D rewrote the Block D subtitle to operator language.
    assert "前置条件与阻塞原因由发布门禁决定，本面板不发明事实。" in source
    # Old wording is retired from operator-facing copy.
    assert "前置条件与阻塞原因来自统一 publish_readiness 上游" not in source


# ---------------------------------------------------------------------------
# Block F "待补齐" mission baseline (Visual Issue #3)
# ---------------------------------------------------------------------------


def test_block_f_need_section_always_renders_mission_baseline() -> None:
    """Visual validation issue #3: 待补齐 must render the mission-
    §B.4 canonical operator-language baseline list, not the raw contract
    kind_label_zh derived from delivery_comprehension."""

    source = _read()
    # The Jinja MUST be the simplified form that always renders the
    # baseline when not publishable.
    assert (
        "{% if ms_publish_readiness.publishable %}—{% else %}{{ ms_block_f_need_baseline | join(\"、\") }}。{% endif %}"
        in source
    )
    # The old "show derived missing items" Jinja branch is retired.
    assert "{% if ms_block_f_missing.items %}{{ ms_block_f_missing.items | join" not in source


def test_block_f_baseline_list_is_mission_canonical() -> None:
    """The baseline list itself is pinned to Mission §B.4 wording."""

    source = _read()
    assert (
        '{% set ms_block_f_need_baseline = ["成片", "字幕", "音频", "manifest", "交付包"] %}'
        in source
    )


# ---------------------------------------------------------------------------
# F · 诊断 fold still carries the engineering identifiers (architect view)
# ---------------------------------------------------------------------------


def test_f_diagnostics_fold_still_present_for_architects() -> None:
    """Quarantine doesn't mean removal — the engineering IDs are still
    accessible inside the collapsed F · 诊断 fold so architects can
    audit when needed."""

    source = _read()
    assert 'data-role="op-console-ms-secondary-fold"' in source
    # Architect-facing summary
    assert "F · 诊断" in source
    assert "矩阵脚本 · 技术诊断（架构师视图，默认收起）" in source

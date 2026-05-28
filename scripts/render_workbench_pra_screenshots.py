"""PR-A reset · render minimal Matrix Script Workbench screenshots.

Renders the `task_workbench.html` matrix_script branch against a
synthetic empty-state context (no media exists — the universal state of
production today) and saves the rendered HTML to the PR-A screenshot
directory. Two HTML snapshots are produced:

  01_pra_workbench_full_default_collapsed.html
      Operator's first-screen experience — Sections 1–4 visible,
      Section 5 (技术诊断) collapsed by default.

  02_pra_workbench_full_section5_expanded.html
      Same context, with `open` injected into the Section 5 <details>
      so the architect view of the retired legacy A–F blocks is visible.

These are RENDERED HTML files (same convention as the prior wave's
`docs/design/screenshots/matrix_script_ui_redesign_2026-05-28/`
snapshots — open in a browser to inspect the visual result).

The renderer uses Jinja2 directly with stubbed presenter outputs; no
FastAPI / no database / no live task lookup. Its job is to exercise the
template's Section 1–5 rendering paths against a representative empty
state, not to reproduce every diagnostic helper's projection.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, FileSystemLoader, select_autoescape


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "gateway" / "app" / "templates"
DEFAULT_OUT_DIR = (
    REPO_ROOT
    / "docs"
    / "design"
    / "screenshots"
    / "matrix_script_workbench_product_flow_reset_2026-05-29"
    / "pra"
)


def _matrix_helpers() -> dict:
    """Synthetic empty-state outputs for the matrix_script workbench
    presenter helpers — enough to exercise the template's Section 1–5
    rendering paths."""

    return {
        "matrix_script_main_video_result": {
            "is_matrix_script": True,
            "state_kind": "not_generated",
            "state_label_zh": "未生成",
            "panel_title_zh": "主视频结果",
            "panel_subtitle_zh": (
                "本任务尚未生成主视频。下方为生产流程与可选变体的观测视图。"
            ),
            "preview": {
                "available": False,
                "variation_id": None,
                "empty_state_message_zh": (
                    "当前尚未生成主视频。已完成脚本结构与生成方案准备，"
                    "成片生成能力接入后将在这里展示视频结果。"
                ),
            },
            "primary_actions": [
                {
                    "action_id": "generate_main_video",
                    "label_zh": "生成主视频",
                    "enabled": False,
                    "disabled_reason_zh": "生成能力接入后开放（资格扩展波）。",
                },
                {
                    "action_id": "regenerate",
                    "label_zh": "重新生成",
                    "enabled": False,
                    "disabled_reason_zh": "生成能力接入后开放。",
                },
                {
                    "action_id": "confirm_main_version",
                    "label_zh": "确认为主版本",
                    "enabled": False,
                    "disabled_reason_zh": "尚无新鲜成片可确认。",
                },
                {
                    "action_id": "go_to_delivery",
                    "label_zh": "前往交付页面",
                    "enabled": True,
                    "href": "/tasks/ms-pra-demo-001/publish",
                },
            ],
            "blocker_one_liner_zh": "当前阻塞:尚未生成主视频。",
            "next_action_one_liner_zh": (
                "下一步:等待生成能力接入;可前往交付页面预览交付清单。"
            ),
            "confirm_note_prefix": "[main-version-confirmed]",
            "closure_event_endpoint_template": (
                "/api/matrix-script/closures/{task_id}/events"
            ),
            "recommended_variation_id": None,
        },
        "matrix_script_script_structure": {
            "is_matrix_script": True,
            "title_value": "PR-A reset 演示任务",
            "target_platform_value": "TikTok",
            "language_scope": {"target_language": ["zh-CN", "en"]},
            "axis_hints": {"audience_hint": "B2C 短视频运营新手"},
            "sections": [
                {
                    "section_id": "hook",
                    "section_label_zh": "Hook · 前 3 秒",
                    "body_status_code": "current_fresh",
                    "body_status_label_zh": "已具备",
                    "body_text": "三秒钩:你的内容值不值得被看完?",
                },
                {
                    "section_id": "body",
                    "section_label_zh": "Body · 中段",
                    "body_status_code": "current_fresh",
                    "body_status_label_zh": "已具备",
                    "body_text": "信息密度:三段式叙事，每段给出明确收益。",
                },
                {
                    "section_id": "cta",
                    "section_label_zh": "CTA · 结尾",
                    "body_status_code": "current_fresh",
                    "body_status_label_zh": "已具备",
                    "body_text": "行动指引:关注 + 评论你的下一个选题。",
                },
            ],
            "taxonomy": [
                {
                    "taxonomy_id": "keywords",
                    "taxonomy_label_zh": "关键词",
                    "values_status_code": "current_fresh",
                    "values_status_label_zh": "已具备",
                    "values": ["内容运营", "短视频"],
                },
                {
                    "taxonomy_id": "banwords",
                    "taxonomy_label_zh": "禁用词",
                    "values_status_code": "current_fresh",
                    "values_status_label_zh": "已具备",
                    "values": ["夸大宣传", "绝对化承诺"],
                },
            ],
        },
        "matrix_script_readable_variants": {
            "is_matrix_script": True,
            "variant_count": 3,
            "variant_candidates_label_zh": "共 3 个候选已派生",
            "variant_candidates": [
                {
                    "differentiator_zh": "节奏更紧凑",
                    "axis_summary_zh": "短时长 · 高密度",
                    "length_hint_zh": "30 秒",
                    "bound_slot_label_zh": "已绑定脚本片段",
                },
                {
                    "differentiator_zh": "口语化更强",
                    "axis_summary_zh": "中时长 · 故事化",
                    "length_hint_zh": "45 秒",
                    "bound_slot_label_zh": "已绑定脚本片段",
                },
                {
                    "differentiator_zh": "信息更完整",
                    "axis_summary_zh": "长时长 · 教学型",
                    "length_hint_zh": "60 秒",
                    "bound_slot_label_zh": "已绑定脚本片段",
                },
            ],
        },
        "matrix_script_recommended_action": {
            "is_matrix_script": True,
            "headline_zh": "建议先确认主视频生成方案。",
            "next_action_zh": "等待生成能力接入;准备就绪后从主视频结果触发生成。",
            "status_kind": "blocked_pending_publish_readiness",
            "status_label_zh": "待生成",
            "head_reason": "missing_final_video",
            "head_reason_label_zh": "尚未生成成片",
            "reason_zh": "本任务的主视频成片能力仍在接入中。",
            "recommended_variant": {"variation_id": "v1"},
        },
        "matrix_script_preview_compare": {
            "is_matrix_script": True,
            "variations": [
                {
                    "variation_id": "v1",
                    "recommended_bucket": "publishable_candidate",
                    "preview_status_code": "unobservable_pending_upstream",
                    "preview_status_label_zh": "暂无可预览成片",
                    "preview_status_explanation_zh": "等待主视频生成。",
                    "recommended_label_zh": "推荐候选",
                },
                {
                    "variation_id": "v2",
                    "recommended_bucket": "alternate_candidate",
                    "preview_status_code": "unobservable_pending_upstream",
                    "preview_status_label_zh": "暂无可预览成片",
                    "preview_status_explanation_zh": "等待主视频生成。",
                    "recommended_label_zh": "备选候选",
                },
                {
                    "variation_id": "v3",
                    "recommended_bucket": "alternate_candidate",
                    "preview_status_code": "unobservable_pending_upstream",
                    "preview_status_label_zh": "暂无可预览成片",
                    "preview_status_explanation_zh": "等待主视频生成。",
                    "recommended_label_zh": "备选候选",
                },
            ],
        },
        "matrix_script_result_summary": {
            "is_matrix_script": True,
            "status_kind": "blocked_pending_publish_readiness",
            "status_label_zh": "未就绪",
            "headline_zh": "尚未生成成片。",
            "head_reason": "missing_final_video",
            "head_reason_label_zh": "尚未生成成片",
            "next_action_zh": "等待生成能力接入。",
        },
        "matrix_script_review_zone": {
            "is_matrix_script": True,
            "zones": [],
            "review_status_rows": [],
            "closure_endpoint_explanation_zh": (
                "提交分区评审意见后，通过现有 closure 端点写入意图记录。"
            ),
        },
        "matrix_script_qc_diagnostics": {
            "is_matrix_script": True,
            "ready_gate_explanation": {
                "publishable": False,
                "publish_ready": False,
                "compose_ready": False,
                "head_reason": "missing_final_video",
                "head_reason_label_zh": "尚未生成成片",
            },
            "risk_items": [],
            "quality_items": [],
            "artifact_status_items": [],
        },
        "matrix_script_delivery_ready_package": {
            "is_matrix_script": True,
            "rows": [],
            "blocked_count": 0,
        },
        "matrix_script_delivery_comprehension": {
            "is_matrix_script": True,
            "lanes": {
                "required_blocking": {"rows": []},
                "required_non_blocking": {"rows": []},
                "optional_non_blocking": {"rows": []},
            },
        },
        "matrix_script_variation_surface": {},
        "matrix_script_comprehension": {},
    }


def build_context() -> dict:
    task = {"task_id": "ms-pra-demo-001", "title": "PR-A reset 演示任务"}
    task_json = {
        "operator_surfaces": {
            "publish_readiness": {
                "publishable": False,
                "head_reason": "missing_final_video",
                "consumed_inputs": {},
            },
            "workbench": {
                "line_specific_panel": {"panel_kind": "matrix_script"},
                **_matrix_helpers(),
            },
            "hot_follow_panel": {},
        }
    }
    return {
        "task": task,
        "task_view": {},
        "task_json": task_json,
        "lang": "zh",
        "current_lang": "zh",
        "languages": [{"code": "zh", "label": "中文"}],
        "i18n_payload": {"lang": "zh", "messages": {}},
        "topbar_subtitle": "工作台 · 矩阵脚本",
        "i18n_label": lambda key, default="", **kw: default or key,
        "t": lambda key, default="", **kw: default or key,
        "request": {"url": {"path": f"/tasks/{task['task_id']}/workbench"}},
        "url_for": lambda name, **kw: "#",
    }


def render(open_section5: bool = False) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(default=True),
        undefined=ChainableUndefined,
    )
    template = env.get_template("task_workbench.html")
    html = template.render(**build_context())
    if open_section5:
        html = html.replace(
            '<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold">',
            '<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold" open>',
            1,
        )
    return html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", default=str(DEFAULT_OUT_DIR), help="Output directory"
    )
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    default_path = out_dir / "01_pra_workbench_full_default_collapsed.html"
    expanded_path = out_dir / "02_pra_workbench_full_section5_expanded.html"

    default_path.write_text(render(open_section5=False), encoding="utf-8")
    expanded_path.write_text(render(open_section5=True), encoding="utf-8")

    print(f"wrote {default_path.relative_to(REPO_ROOT)}")
    print(f"wrote {expanded_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

"""PR-B reset · render Matrix Script Delivery Center HTML screenshots.

Two snapshots:

  01_prb_delivery_center_full_default_collapsed.html
      Operator first-scan: Sections 1–6 visible, Section 7 (技术诊断)
      collapsed by default.

  02_prb_delivery_center_full_section7_expanded.html
      Same context, Section 7 forced open via `open` attribute injection.

Snapshots render against a synthetic empty-state context (no media yet —
the universal state of production today).
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
    / "prb"
)


def _ms_pub() -> dict:
    return {
        "is_matrix_script": True,
        "closure_endpoint_url": "/api/matrix-script/closures/ms-prb-demo-001/events",
        "eight_stage_state": {
            "stage": "awaiting_review",
            "stage_index": 3,
            "stage_label": "待校对",
        },
        "task_area_result_status": {
            "status_kind": "blocked_pending_publish_readiness",
            "status_label_zh": "未就绪",
            "headline_zh": "尚未生成成片。",
        },
        "publish_readiness": {
            "publishable": False,
            "head_reason": "missing_final_video",
            "consumed_inputs": {},
        },
        "delivery_comprehension": {
            "is_matrix_script": True,
            "final_video_primary": {
                "title_zh": "主视频",
                "subtitle_zh": "本任务的核心交付物。",
            },
            "lanes": {
                "required_blocking": {
                    "rows": [
                        {
                            "kind": "subtitle",
                            "kind_label_zh": "字幕",
                            "artifact_status_code": "unobservable_pending_upstream",
                            "artifact_status_label_zh": "尚未具备",
                            "zoning_label_zh": "必需 · 阻塞发布",
                            "artifact_status_explanation_zh": "等待主视频生成。",
                        },
                        {
                            "kind": "dub",
                            "kind_label_zh": "音频",
                            "artifact_status_code": "unobservable_pending_upstream",
                            "artifact_status_label_zh": "尚未具备",
                            "zoning_label_zh": "必需 · 阻塞发布",
                            "artifact_status_explanation_zh": "等待主视频生成。",
                        },
                        {
                            "kind": "manifest",
                            "kind_label_zh": "manifest",
                            "artifact_status_code": "unobservable_pending_upstream",
                            "artifact_status_label_zh": "尚未具备",
                            "zoning_label_zh": "必需 · 阻塞发布",
                            "artifact_status_explanation_zh": "等待生成。",
                        },
                        {
                            "kind": "delivery_pack",
                            "kind_label_zh": "交付包",
                            "artifact_status_code": "unobservable_pending_upstream",
                            "artifact_status_label_zh": "尚未具备",
                            "zoning_label_zh": "必需 · 阻塞发布",
                            "artifact_status_explanation_zh": "等待打包。",
                        },
                    ],
                    "row_count": 4,
                },
                "required_non_blocking": {
                    "rows": [
                        {
                            "kind": "copy_bundle",
                            "kind_label_zh": "文案包",
                            "artifact_status_code": "current_fresh",
                            "artifact_status_label_zh": "已具备",
                            "zoning_label_zh": "必需 · 不阻塞",
                            "artifact_status_explanation_zh": "—",
                        },
                    ],
                    "row_count": 1,
                },
                "optional_non_blocking": {
                    "rows": [
                        {
                            "kind": "scene_pack",
                            "kind_label_zh": "场景包",
                            "artifact_status_code": "unobservable_pending_upstream",
                            "artifact_status_label_zh": "未生成",
                        },
                    ],
                    "row_count": 1,
                },
            },
        },
        "preview_compare": {
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
                    "recommended_label_zh": "备选",
                },
                {
                    "variation_id": "v3",
                    "recommended_bucket": "alternate_candidate",
                    "preview_status_code": "unobservable_pending_upstream",
                    "preview_status_label_zh": "暂无可预览成片",
                    "preview_status_explanation_zh": "等待主视频生成。",
                    "recommended_label_zh": "备选",
                },
            ],
        },
        "recommended_action": {
            "is_matrix_script": True,
            "headline_zh": "建议先确认主视频生成方案。",
            "next_action_zh": "等待生成能力接入；准备就绪后从工作台触发生成。",
            "status_kind": "blocked_pending_publish_readiness",
            "status_label_zh": "待生成",
            "head_reason": "missing_final_video",
            "head_reason_label_zh": "尚未生成成片",
            "reason_zh": "本任务的主视频成片能力仍在接入中。",
            "recommended_variant": {},
        },
        "delivery_ready_package": {"rows": [], "blocked_count": 0},
        "delivery_copy_bundle": {
            "subfields": [
                {
                    "subfield_id": "title",
                    "label_zh": "标题",
                    "status_code": "resolved_from_existing_projection",
                    "value": "PR-B reset 演示任务",
                },
            ],
            "tracked_gap_summary_zh": "其他文案待生成。",
            "panel_subtitle_zh": "标题 / Hashtags / CTA / 评论关键词。",
        },
        "publish_backfill_readiness": {"rows": [], "row_count": 0},
        "publish_feedback_closure": {
            "variation_feedback": [],
            "feedback_closure_records": [],
        },
    }


def build_context() -> dict:
    task = {
        "task_id": "ms-prb-demo-001",
        "title": "PR-B reset 演示任务",
        "category_key": "matrix_script",
        "kind": "matrix_script",
        "platform": "matrix_script",
    }
    return {
        "task": task,
        "task_view": {},
        "task_json": {"operator_surfaces": {}},
        "lang": "zh",
        "current_lang": "zh",
        "languages": [{"code": "zh", "label": "中文"}],
        "i18n_payload": {"lang": "zh", "messages": {}},
        "topbar_subtitle": "交付中心 · 矩阵脚本",
        "i18n_label": lambda key, default="", **kw: default or key,
        "t": lambda key, default="", **kw: default or key,
        "request": {"url": {"path": f"/tasks/{task['task_id']}/publish"}},
        "url_for": lambda name, **kw: "#",
        "ms_publish_hub": _ms_pub(),
        "task_id": task["task_id"],
    }


def render(open_section7: bool = False) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(default=True),
        undefined=ChainableUndefined,
    )
    template = env.get_template("task_publish_hub.html")
    html = template.render(**build_context())
    if open_section7:
        html = html.replace(
            '<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold">',
            '<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold" open>',
            1,
        )
    return html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    default_path = out_dir / "01_prb_delivery_center_full_default_collapsed.html"
    expanded_path = out_dir / "02_prb_delivery_center_full_section7_expanded.html"

    default_path.write_text(render(open_section7=False), encoding="utf-8")
    expanded_path.write_text(render(open_section7=True), encoding="utf-8")

    print(f"wrote {default_path.relative_to(REPO_ROOT)}")
    print(f"wrote {expanded_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

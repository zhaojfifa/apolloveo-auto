"""PR-B · Matrix Script Operator Workbench Flow Alignment tests.

Proves the linked operator view model (script → storyboard → materials → voice →
subtitles/music → variants → delivery) and that the rendered operator-flow
section reflects the operator-usable result instead of an isolated technical
card. Pure presenter; no schema/contract, no provider/publish leakage.
"""
from __future__ import annotations

import re

import pytest

from gateway.app.services.matrix_script.operator_workbench_view import (
    build_matrix_script_operator_workbench_view,
)

TASK = {"task_id": "ms-flow-1", "kind": "matrix_script", "config": {"entry": {}}}

# A PR-A operator-usable result (the tomato partial_pass verdict).
USABLE_RESULT = {
    "has_result": True,
    "operator_usable": True,
    "technical_preview": False,
    "delivery_candidate": True,
    "official_publish_ready": False,
    "visual_semantic_match": "partial_pass",
    "shot_count": 5,
    "shot_match_count": 3,
    "real_visual_count": 3,
    "blocked_reason": None,
    "caption_mode": "burned_in",
    "preview_url": "/api/matrix-script/ms-flow-1/tomato-real-result/preview/final.mp4",
}

FALLBACK_RESULT = {
    "has_result": True,
    "operator_usable": False,
    "technical_preview": True,
    "delivery_candidate": False,
    "official_publish_ready": False,
    "visual_semantic_match": "failed",
    "shot_count": 5,
    "shot_match_count": 0,
    "real_visual_count": 0,
    "blocked_reason": "fallback_only_or_missing_real_visuals",
}


# 1. main result uses the operator_usable result when present
def test_main_result_uses_operator_usable_result() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    mr = v["main_result"]
    assert mr["status"] == "operator_usable"
    assert mr["operator_usable"] is True
    assert mr["technical_preview"] is False
    assert mr["visual_semantic_match"] == "partial_pass"
    assert mr["shot_match_count"] == 3 and mr["shot_count"] == 5
    assert mr["real_visual_count"] == 3
    assert mr["delivery_candidate"] is True
    assert mr["official_publish_ready"] is False
    assert mr["current_variant"] == "V1 清新种草版"


def test_main_result_not_generated_when_no_result() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=None, env={})
    assert v["main_result"]["status"] == "not_generated"
    assert v["main_result"]["next_step_zh"]


def test_main_result_technical_preview_on_fallback() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=FALLBACK_RESULT, env={})
    mr = v["main_result"]
    assert mr["status"] == "technical_preview"
    assert mr["operator_usable"] is False
    assert mr["delivery_candidate"] is False
    assert mr["blocked_reason"] == "fallback_only_or_missing_real_visuals"


# 2. rendered main result does not show 未生成 / 主成片缺失 when operator_usable=true
def _render_flow_section(view) -> str:
    from jinja2 import Environment, ChainableUndefined

    src = open("gateway/app/templates/task_workbench.html", encoding="utf-8").read()
    start = src.index("{% if ms_flow.is_matrix_script %}")
    end = src.index("</section>", start) + len("</section>")
    block = src[start:end] + "\n{% endif %}"
    env = Environment(undefined=ChainableUndefined, autoescape=True)
    return env.from_string(block).render(ms_flow=view, task=TASK)


def test_rendered_main_result_no_not_generated_when_usable() -> None:
    view = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    html = _render_flow_section(view)
    # Section A reflects operator-usable; the main-result card must not claim
    # 未生成 / 主成片缺失 when a usable result exists.
    main_card = html[html.index('data-role="ms-flow-main-result"'):html.index('data-role="ms-flow-script-understanding"')]
    assert "运营可用" in main_card
    assert "未生成" not in main_card
    assert "主成片缺失" not in main_card


# 3 + 4. storyboard shows 5 shots, each with source + semantic status
def test_storyboard_five_shots_with_source_and_semantic() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    sb = v["storyboard"]
    assert len(sb) == 5
    for card in sb:
        assert card["source"] in ("local_real_asset", "fallback_semantic_reuse")
        assert card["semantic_status"] in ("pass", "partial")
    # 3 real → pass, 2 reuse → partial
    assert sum(1 for c in sb if c["semantic_status"] == "pass") == 3
    assert sum(1 for c in sb if c["semantic_status"] == "partial") == 2
    assert all(c["included_in_current_video"] for c in sb)  # result present


# 5. materials map asset files → shots
def test_materials_map_assets_to_shots() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    mats = {m["asset_name"]: m for m in v["materials"]}
    assert set(mats) == {"01_beach_hook.png", "02_tomato_bowl.png", "03_pick_tomato.png"}
    assert mats["02_tomato_bowl.png"]["used_by"] == ["shot02", "shot05"]
    assert mats["03_pick_tomato.png"]["used_by"] == ["shot03", "shot04"]
    assert mats["01_beach_hook.png"]["used_by"] == ["shot01"]


# 6. voice shows azure when env present, fallback otherwise
def test_voice_azure_when_env_present() -> None:
    v = build_matrix_script_operator_workbench_view(
        TASK, result=USABLE_RESULT,
        env={"AZURE_SPEECH_KEY": "k", "AZURE_SPEECH_REGION": "eastasia"},
    )
    assert v["voice"]["provider"] == "azure"
    assert v["voice"]["status"] == "ready"
    assert v["voice"]["blocked_reason"] is None


def test_voice_fallback_when_no_env() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    assert v["voice"]["provider"] == "fallback"
    assert v["voice"]["status"] == "fallback"
    assert v["voice"]["blocked_reason"] == "missing_azure_env"


# 7. subtitles/music shows subtitle state
def test_subtitles_music_state() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    sm = v["subtitles_music"]
    assert sm["subtitles"] == "generated"
    assert sm["burned_captions"] is True
    assert sm["bgm"] == "none"


# 8. variants: V1 generated, V2/V3 pending
def test_variants_v1_generated_v2_v3_pending() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    by_id = {x["id"]: x for x in v["variants"]}
    assert by_id["v1"]["status"] == "generated"
    assert by_id["v2"]["status"] == "pending"
    assert by_id["v3"]["status"] == "pending"


def test_variant_v1_ready_when_no_result() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=None, env={})
    by_id = {x["id"]: x for x in v["variants"]}
    assert by_id["v1"]["status"] == "ready_to_generate"


# 9. delivery shows V1 candidate + official_publish_ready false
def test_delivery_entry() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    d = v["delivery"]
    assert d["candidate_variant"] == "v1"
    assert d["delivery_candidate"] is True
    assert d["official_publish_ready"] is False


# 10. no provider/publish/vendor leakage in the view model
def test_no_forbidden_token_leakage() -> None:
    for res in (None, USABLE_RESULT, FALLBACK_RESULT):
        v = build_matrix_script_operator_workbench_view(TASK, result=res, env={})
        blob = str(v).lower()
        for token in ("provider_url", "temporary_url", "download_url", "akool",
                      "vendor", "model_id", "credit", "publish_url", "publish_status",
                      "http://", "https://"):
            assert token not in blob


# main result derives from the staged candidate on task config when no explicit result
def test_main_result_from_staged_candidate_on_config() -> None:
    task = {"task_id": "ms-flow-2", "kind": "matrix_script",
            "config": {"matrix_script_staged_candidate": USABLE_RESULT}}
    v = build_matrix_script_operator_workbench_view(task, env={})
    assert v["main_result"]["status"] == "operator_usable"


# 11 (module-boundary): helper imports no forbidden runtime modules. (The word
# "akool" legitimately appears in the helper's own forbidden-token GUARD list,
# so we assert on import statements, not raw substrings — leakage into output is
# covered by test_no_forbidden_token_leakage.)
def test_helper_module_boundary() -> None:
    import gateway.app.services.matrix_script.operator_workbench_view as mod
    src = open(mod.__file__, encoding="utf-8").read()
    import_lines = [ln for ln in src.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    joined = "\n".join(import_lines)
    for forbidden in ("artifact_storage", "hot_follow", "digital_anchor", "akool",
                      "schemas", "contracts"):
        assert forbidden not in joined

"""Matrix Script shot-plan skeleton tests (Phase 3 PR-2).

Covers ``gateway/app/services/matrix_script/shot_plan.py`` and
``shot_plan_builder.py``:

- deterministic 4–8 shot generation from a Hook / Body / CTA outline
- duration distribution within tolerance of the requested target
- every shot carries the required business-intent fields
- ``generation_mode`` is drawn only from the closed local set
- the serialized plan leaks no provider / vendor / model / credit token and
  no ``final_video`` / artifact-truth field
- empty / contentless outline fails clearly
- determinism: identical input → identical plan
- the modules import no Akool / provider / adapter dependency
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script import shot_plan as shot_plan_module
from gateway.app.services.matrix_script import shot_plan_builder as builder_module
from gateway.app.services.matrix_script.shot_plan import (
    GENERATION_MODE_AVATAR_SEGMENT,
    GENERATION_MODES,
    MAX_SHOTS,
    MIN_SHOTS,
    MatrixScriptShotPlan,
    ShotPlanError,
    shot_plan_to_dict,
)
from gateway.app.services.matrix_script.shot_plan_builder import build_shot_plan


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def _outline(**overrides):
    base = {
        "hook": "3 秒讲清楚这个产品解决什么问题",
        "body": [
            "展示使用前的痛点场景",
            "演示产品的关键操作",
            "对比使用前后的效果",
        ],
        "cta": "点击主页链接，评论区告诉我你的需求",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. builds 4–8 shots
# ---------------------------------------------------------------------------


def test_builds_4_to_8_shots_from_valid_outline() -> None:
    plan = build_shot_plan(_outline(), task_id="task-1")
    assert isinstance(plan, MatrixScriptShotPlan)
    assert MIN_SHOTS <= len(plan.shots) <= MAX_SHOTS
    # 3 body points + hook + cta = 5
    assert len(plan.shots) == 5


def test_single_body_point_still_reaches_minimum_shots() -> None:
    plan = build_shot_plan(_outline(body="只有一个要点"), task_id="t")
    assert len(plan.shots) >= MIN_SHOTS


def test_many_body_points_clamp_to_maximum_shots() -> None:
    plan = build_shot_plan(_outline(body=[f"要点 {i}" for i in range(20)]), task_id="t")
    assert len(plan.shots) == MAX_SHOTS


def test_shot_orders_are_contiguous() -> None:
    plan = build_shot_plan(_outline(), task_id="t")
    assert [s.order for s in plan.shots] == list(range(1, len(plan.shots) + 1))


# ---------------------------------------------------------------------------
# 2. duration within tolerance
# ---------------------------------------------------------------------------


def test_total_duration_fits_target_within_tolerance() -> None:
    plan = build_shot_plan(_outline(), task_id="t", target_duration_seconds=40.0)
    assert abs(plan.total_duration_seconds - 40.0) <= 0.5
    assert all(s.duration_seconds > 0 for s in plan.shots)


# ---------------------------------------------------------------------------
# 3. required per-shot fields present
# ---------------------------------------------------------------------------


def test_every_shot_has_required_business_fields() -> None:
    plan = build_shot_plan(_outline(), task_id="t")
    for s in plan.shots:
        assert s.visual_intent.strip()
        assert s.audio_text.strip()
        assert s.subtitle_text.strip()
        assert s.asset_need.strip()
        assert s.action.strip()
        assert s.scene_context.strip()


# ---------------------------------------------------------------------------
# 4. generation_mode closed set
# ---------------------------------------------------------------------------


def test_generation_mode_is_from_closed_set() -> None:
    plan = build_shot_plan(_outline(), task_id="t")
    for s in plan.shots:
        assert s.generation_mode in GENERATION_MODES


def test_role_drives_avatar_hook_and_role_attribution() -> None:
    plan = build_shot_plan(_outline(role="品牌主理人"), task_id="t")
    hook = plan.shots[0]
    assert hook.generation_mode == GENERATION_MODE_AVATAR_SEGMENT
    assert hook.role == "品牌主理人"
    # non-avatar shots carry no role
    for s in plan.shots[1:]:
        if s.generation_mode != GENERATION_MODE_AVATAR_SEGMENT:
            assert s.role is None


# ---------------------------------------------------------------------------
# 5 + 6. no provider/vendor/model/credit + no artifact-truth leakage
# ---------------------------------------------------------------------------


def test_serialized_plan_has_no_provider_or_artifact_tokens() -> None:
    plan = build_shot_plan(_outline(role="主理人"), task_id="t")
    blob = json.dumps(shot_plan_to_dict(plan), ensure_ascii=False).lower()
    for token in (
        "akool",
        "provider",
        "vendor",
        "model_id",
        "credit",
        "provider_task_id",
        "temporary_url",
        "final_video",
        "artifact_key",
    ):
        assert token not in blob, f"serialized shot plan leaks '{token}'"


def test_serialized_plan_has_no_artifact_truth_keys() -> None:
    plan = build_shot_plan(_outline(), task_id="t")
    d = shot_plan_to_dict(plan)
    assert "final_video" not in d
    assert "artifact_key" not in d
    assert "deliverable" not in d
    for s in d["shots"]:
        assert "final_video" not in s
        assert "artifact_key" not in s


def test_validate_shot_plan_guard_rejects_forbidden_token() -> None:
    # A hand-built plan whose content embeds a forbidden token must be caught
    # by the defensive guard (truth-source discipline).
    from gateway.app.services.matrix_script.shot_plan import (
        MatrixScriptShotSpec,
        assert_no_forbidden_tokens,
    )

    bad = MatrixScriptShotPlan(
        plan_id="shotplan-bad",
        task_id="t",
        aspect_ratio="9:16",
        target_duration_seconds=30.0,
        shots=tuple(
            MatrixScriptShotSpec(
                shot_id=f"shotplan-bad-{i:02d}",
                order=i,
                duration_seconds=7.5,
                role=None,
                visual_intent="x" if i != 1 else "uses akool provider",
                action="a",
                scene_context="body",
                asset_need="still",
                audio_text="t",
                subtitle_text="t",
                generation_mode="static_asset",
            )
            for i in range(1, 5)
        ),
        source_outline_ref=None,
    )
    with pytest.raises(ShotPlanError):
        assert_no_forbidden_tokens(bad)


# ---------------------------------------------------------------------------
# 7. empty outline fails clearly
# ---------------------------------------------------------------------------


def test_empty_outline_fails_clearly() -> None:
    with pytest.raises(ShotPlanError):
        build_shot_plan({}, task_id="t")


def test_missing_hook_fails_clearly() -> None:
    with pytest.raises(ShotPlanError):
        build_shot_plan({"body": ["x"], "cta": "y"}, task_id="t")


def test_missing_cta_fails_clearly() -> None:
    with pytest.raises(ShotPlanError):
        build_shot_plan({"hook": "h", "body": ["x"]}, task_id="t")


def test_blank_body_points_fail_clearly() -> None:
    with pytest.raises(ShotPlanError):
        build_shot_plan({"hook": "h", "body": ["", "   "], "cta": "c"}, task_id="t")


# ---------------------------------------------------------------------------
# 8. determinism
# ---------------------------------------------------------------------------


def test_same_input_produces_same_plan() -> None:
    a = build_shot_plan(_outline(), task_id="task-x")
    b = build_shot_plan(_outline(), task_id="task-x")
    assert shot_plan_to_dict(a) == shot_plan_to_dict(b)
    assert a.plan_id == b.plan_id


def test_different_input_produces_different_plan_id() -> None:
    a = build_shot_plan(_outline(), task_id="task-x")
    b = build_shot_plan(_outline(hook="完全不同的钩子"), task_id="task-x")
    assert a.plan_id != b.plan_id


# ---------------------------------------------------------------------------
# 9. no Akool / provider / adapter dependency
# ---------------------------------------------------------------------------


def test_modules_import_no_akool_or_provider_or_adapter() -> None:
    for mod in (shot_plan_module, builder_module):
        src = inspect.getsource(mod)
        assert "providers.akool" not in src
        assert "workers.adapters" not in src
        assert "import httpx" not in src
        assert "from swiftcraft" not in src
        assert "import swiftcraft" not in src
        # no runtime / route / storage / packet reach
        for token in (
            "gateway.app.routers",
            "gateway.app.services.packet",
            "artifact_storage",
            "compose_service",
            "os.environ",
            "os.getenv",
        ):
            assert token not in src, f"module leaks into {token}"

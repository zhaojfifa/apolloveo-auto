"""Matrix Script scene artifact / manifest skeleton tests (Phase 3 PR-3).

Covers ``gateway/app/services/matrix_script/scene_artifacts.py`` and
``scene_manifest.py``:

- one planned scene slot per shot, order-preserving, deterministic filenames
- deterministic manifest skeleton
- no artifact-truth field (key / url / exists / ready / delivered / task_id)
- no provider / vendor / model / credit leakage
- scene_pack non-blocking; final_video required as expectation but not created
- modules import no Akool / provider / adapter / storage dependency
- invalid shot plan fails clearly
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script import scene_artifacts as scene_artifacts_module
from gateway.app.services.matrix_script import scene_manifest as scene_manifest_module
from gateway.app.services.matrix_script.scene_artifacts import (
    EXPECTED_KIND_SCENE_SEGMENT,
    SLOT_STATUS_PLANNED,
    MatrixScriptSceneArtifactSlot,
    SceneArtifactError,
    build_scene_artifact_slots,
    scene_slot_to_dict,
)
from gateway.app.services.matrix_script.scene_manifest import (
    MatrixScriptSceneManifestSkeleton,
    build_scene_manifest_skeleton,
    scene_manifest_to_dict,
)
from gateway.app.services.matrix_script.shot_plan_builder import build_shot_plan

_FORBIDDEN_TRUTH_TOKENS = (
    "akool",
    "provider",
    "vendor",
    "model_id",
    "credit",
    "provider_task_id",
    "provider_url",
    "temporary_url",
    "download_url",
    "artifact_key",
    "final_video_key",
    "publish_ready",
    "delivered",
)


def _plan(**overrides):
    outline = {
        "hook": "前 3 秒讲清楚价值",
        "body": ["展示痛点", "演示操作", "对比效果"],
        "cta": "评论区告诉我你的需求",
    }
    outline.update(overrides.pop("outline", {}))
    return build_shot_plan(outline, task_id=overrides.get("task_id", "task-1"))


# ---------------------------------------------------------------------------
# 1 + 2 + 3. one slot per shot, order preserved, deterministic filenames
# ---------------------------------------------------------------------------


def test_one_planned_slot_per_shot() -> None:
    plan = _plan()
    slots = build_scene_artifact_slots(plan)
    assert len(slots) == len(plan.shots)
    assert all(s.status == SLOT_STATUS_PLANNED for s in slots)
    assert all(s.expected_kind == EXPECTED_KIND_SCENE_SEGMENT for s in slots)


def test_slots_preserve_shot_ordering_and_shot_ids() -> None:
    plan = _plan()
    slots = build_scene_artifact_slots(plan)
    assert [s.order for s in slots] == [sh.order for sh in plan.shots]
    assert [s.shot_id for s in slots] == [sh.shot_id for sh in plan.shots]


def test_expected_filenames_are_deterministic_and_zero_padded() -> None:
    plan = _plan()
    slots = build_scene_artifact_slots(plan)
    assert [s.expected_filename for s in slots[:3]] == [
        "scene_001.mp4",
        "scene_002.mp4",
        "scene_003.mp4",
    ]


# ---------------------------------------------------------------------------
# 4. manifest determinism
# ---------------------------------------------------------------------------


def test_manifest_skeleton_is_deterministic() -> None:
    a = build_scene_manifest_skeleton(_plan())
    b = build_scene_manifest_skeleton(_plan())
    assert scene_manifest_to_dict(a) == scene_manifest_to_dict(b)
    assert a.manifest_id == b.manifest_id


def test_manifest_id_tracks_plan_id() -> None:
    plan = _plan()
    manifest = build_scene_manifest_skeleton(plan)
    assert manifest.plan_id == plan.plan_id
    assert manifest.manifest_id == f"manifest-{plan.plan_id}"


# ---------------------------------------------------------------------------
# 5 + 6. no artifact-truth fields / no provider leakage
# ---------------------------------------------------------------------------


def test_serialized_slot_has_no_artifact_truth_fields() -> None:
    plan = _plan()
    slot = build_scene_artifact_slots(plan)[0]
    d = scene_slot_to_dict(slot)
    for forbidden_key in (
        "artifact_key",
        "final_video_key",
        "download_url",
        "provider_url",
        "temporary_url",
        "exists",
        "ready",
        "delivered",
        "publish_ready",
        "provider_task_id",
    ):
        assert forbidden_key not in d


def test_serialized_manifest_has_no_forbidden_tokens() -> None:
    manifest = build_scene_manifest_skeleton(_plan(task_id="t"))
    blob = json.dumps(scene_manifest_to_dict(manifest), ensure_ascii=False).lower()
    for token in _FORBIDDEN_TRUTH_TOKENS:
        assert token not in blob, f"manifest leaks '{token}'"


def test_serialized_manifest_has_no_artifact_truth_keys() -> None:
    manifest = build_scene_manifest_skeleton(_plan())
    d = scene_manifest_to_dict(manifest)
    for forbidden_key in ("final_video_key", "artifact_key", "download_url", "exists", "delivered"):
        assert forbidden_key not in d
    for slot in d["scene_slots"]:
        for forbidden_key in ("artifact_key", "download_url", "provider_url", "exists"):
            assert forbidden_key not in slot


# ---------------------------------------------------------------------------
# 7. scene_pack non-blocking
# ---------------------------------------------------------------------------


def test_scene_pack_blocking_not_allowed_by_default() -> None:
    manifest = build_scene_manifest_skeleton(_plan())
    assert manifest.scene_pack_blocking_allowed is False


def test_scene_slots_are_never_publish_blocking() -> None:
    # intermediate scene segments must never directly block publish
    plan = _plan()
    for slot in build_scene_artifact_slots(plan):
        assert slot.blocking_publish is False


def test_slot_rejects_blocking_publish_true() -> None:
    with pytest.raises(SceneArtifactError):
        MatrixScriptSceneArtifactSlot(
            slot_id="s-01",
            shot_id="sh-01",
            order=1,
            expected_kind=EXPECTED_KIND_SCENE_SEGMENT,
            expected_filename="scene_001.mp4",
            generation_mode="static_asset",
            required_for_final=True,
            blocking_publish=True,
        )


# ---------------------------------------------------------------------------
# 8. final_video required-as-expectation but not created
# ---------------------------------------------------------------------------


def test_final_video_required_is_expectation_only_no_artifact_created() -> None:
    manifest = build_scene_manifest_skeleton(_plan())
    assert manifest.final_video_required is True
    assert manifest.final_video_expected_filename == "final.mp4"
    d = scene_manifest_to_dict(manifest)
    # expectation present, but no real final-video truth
    assert d["final_video_required"] is True
    assert "final_video_key" not in d
    assert "download_url" not in d
    assert "exists" not in d


# ---------------------------------------------------------------------------
# 9. no Akool / provider / adapter / storage dependency
# ---------------------------------------------------------------------------


def test_modules_import_no_akool_provider_adapter_or_storage() -> None:
    for mod in (scene_artifacts_module, scene_manifest_module):
        src = inspect.getsource(mod)
        assert "providers.akool" not in src
        assert "workers.adapters" not in src
        assert "import httpx" not in src
        assert "from swiftcraft" not in src
        assert "import swiftcraft" not in src
        # import/call forms only (the forbidden APIs may be named in docstring
        # prose describing the boundary; what matters is no actual import/call).
        for token in (
            "import artifact_storage",
            "artifact_storage import",
            "upload_artifact(",
            "object_exists(",
            "object_head(",
            "get_download_url(",
            "compose_service",
            "gateway.app.routers",
            "gateway.app.services.packet",
            "os.environ",
            "os.getenv",
            "open(",
            ".write(",
        ):
            assert token not in src, f"module leaks into {token}"


# ---------------------------------------------------------------------------
# 10. invalid shot plan fails clearly
# ---------------------------------------------------------------------------


def test_build_slots_rejects_non_plan() -> None:
    with pytest.raises(SceneArtifactError):
        build_scene_artifact_slots({"not": "a plan"})  # type: ignore[arg-type]


def test_build_manifest_rejects_non_plan() -> None:
    with pytest.raises(SceneArtifactError):
        build_scene_manifest_skeleton(None)  # type: ignore[arg-type]


def test_manifest_rejects_scene_pack_blocking_true() -> None:
    plan = _plan()
    slots = build_scene_artifact_slots(plan)
    with pytest.raises(SceneArtifactError):
        MatrixScriptSceneManifestSkeleton(
            manifest_id="m-1",
            plan_id=plan.plan_id,
            task_id=plan.task_id,
            aspect_ratio=plan.aspect_ratio,
            target_duration_seconds=plan.target_duration_seconds,
            scene_slots=slots,
            scene_pack_blocking_allowed=True,
        )

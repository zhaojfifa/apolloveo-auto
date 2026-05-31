"""Matrix Script scene-manifest skeleton — PRE-RUNTIME (PR-3).

Assembles PR-2 shot-plan + PR-3 scene artifact slots into a deterministic
**manifest skeleton**: the planned set of scene-segment slots plus the
manifest-level *expectation* that a final video and the standard deliverables
will eventually exist. The manifest skeleton does NOT claim any artifact
exists, does NOT generate media, and is NOT deliverable truth.

Authority:
- ``docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`` §6
  (manifest = per-shot artifact list + final.mp4 handle + per-deliverable
  required / blocking_publish; provider URL never deliverable; copy-into-Apollo
  is a later gated step).
- ``docs/contracts/factory_delivery_contract_v1.md`` (``scene_pack_blocking_allowed: false``).
- PR-3 ``scene_artifacts.py``.

Hard boundary: NO Akool / provider / adapter import; NO ``artifact_storage``;
NO file/storage write; NO ``final.mp4`` generation; NO artifact-truth field
(``artifact_key`` / ``final_video_key`` / ``download_url`` / ``provider_url`` /
``temporary_url`` / ``exists`` / ``delivered`` / ``publish_ready`` /
``provider_task_id``). ``final_video_required`` is an *expectation* flag — the
manifest expects a final video but never creates one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from gateway.app.services.matrix_script.scene_artifacts import (
    MatrixScriptSceneArtifactSlot,
    SceneArtifactError,
    assert_no_forbidden_tokens,
    build_scene_artifact_slots,
    scene_slot_to_dict,
)
from gateway.app.services.matrix_script.shot_plan import MatrixScriptShotPlan

# Per factory_delivery_contract_v1 §"Scene-Pack Non-Blocking Rule": scene_pack
# may never block publish at the delivery contract layer.
SCENE_PACK_BLOCKING_ALLOWED = False

# Planned final-video filename (a planned name only — NOT an artifact key/url).
FINAL_VIDEO_EXPECTED_FILENAME = "final.mp4"


@dataclass(frozen=True)
class MatrixScriptSceneManifestSkeleton:
    """Planned manifest for a Matrix Script shot plan. Pre-runtime, not truth.

    ``final_video_required`` records the *expectation* that the line must
    eventually produce a final video; it does not assert one exists.
    """

    manifest_id: str
    plan_id: str
    task_id: Optional[str]
    aspect_ratio: str
    target_duration_seconds: float
    scene_slots: Tuple[MatrixScriptSceneArtifactSlot, ...]
    final_video_required: bool = True
    final_video_expected_filename: str = FINAL_VIDEO_EXPECTED_FILENAME
    scene_pack_blocking_allowed: bool = SCENE_PACK_BLOCKING_ALLOWED

    def __post_init__(self) -> None:
        _require_nonempty_str("manifest_id", self.manifest_id)
        _require_nonempty_str("plan_id", self.plan_id)
        if self.task_id is not None and not isinstance(self.task_id, str):
            raise SceneArtifactError("task_id must be a string or None")
        _require_nonempty_str("aspect_ratio", self.aspect_ratio)
        if (
            isinstance(self.target_duration_seconds, bool)
            or not isinstance(self.target_duration_seconds, (int, float))
            or self.target_duration_seconds <= 0
        ):
            raise SceneArtifactError("target_duration_seconds must be a positive number")
        if not isinstance(self.scene_slots, tuple) or not self.scene_slots:
            raise SceneArtifactError("scene_slots must be a non-empty tuple")
        for slot in self.scene_slots:
            if not isinstance(slot, MatrixScriptSceneArtifactSlot):
                raise SceneArtifactError("scene_slots must contain MatrixScriptSceneArtifactSlot")
        orders = [s.order for s in self.scene_slots]
        if orders != list(range(1, len(self.scene_slots) + 1)):
            raise SceneArtifactError("scene slot orders must be contiguous 1..N")
        if not isinstance(self.final_video_required, bool):
            raise SceneArtifactError("final_video_required must be a bool")
        _require_nonempty_str("final_video_expected_filename", self.final_video_expected_filename)
        # scene_pack must never be allowed to block publish.
        if self.scene_pack_blocking_allowed is not False:
            raise SceneArtifactError("scene_pack_blocking_allowed must be False")


def _require_nonempty_str(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SceneArtifactError(f"{name} must be a non-empty string")


def scene_manifest_to_dict(manifest: MatrixScriptSceneManifestSkeleton) -> Dict[str, Any]:
    """Pure serialization (closed key set; no artifact-truth / provider field).

    Intentionally has no ``final_video_key`` / ``artifact_key`` / ``download_url``
    / ``exists`` / ``delivered`` key — the manifest is a plan, not truth.
    """
    return {
        "manifest_id": manifest.manifest_id,
        "plan_id": manifest.plan_id,
        "task_id": manifest.task_id,
        "aspect_ratio": manifest.aspect_ratio,
        "target_duration_seconds": manifest.target_duration_seconds,
        "final_video_required": manifest.final_video_required,
        "final_video_expected_filename": manifest.final_video_expected_filename,
        "scene_pack_blocking_allowed": manifest.scene_pack_blocking_allowed,
        "scene_slots": [scene_slot_to_dict(s) for s in manifest.scene_slots],
    }


def assert_manifest_has_no_forbidden_tokens(
    manifest: MatrixScriptSceneManifestSkeleton,
) -> None:
    """Defensive guard: serialized manifest carries no truth/provider token."""
    assert_no_forbidden_tokens(repr(scene_manifest_to_dict(manifest)))


def build_scene_manifest_skeleton(
    plan: MatrixScriptShotPlan,
) -> MatrixScriptSceneManifestSkeleton:
    """Build a deterministic manifest skeleton from a shot plan. Pure, no I/O."""
    if not isinstance(plan, MatrixScriptShotPlan):
        raise SceneArtifactError("plan must be a MatrixScriptShotPlan")
    slots = build_scene_artifact_slots(plan)
    manifest = MatrixScriptSceneManifestSkeleton(
        manifest_id=f"manifest-{plan.plan_id}",
        plan_id=plan.plan_id,
        task_id=plan.task_id,
        aspect_ratio=plan.aspect_ratio,
        target_duration_seconds=float(plan.target_duration_seconds),
        scene_slots=slots,
        final_video_required=True,
        final_video_expected_filename=FINAL_VIDEO_EXPECTED_FILENAME,
        scene_pack_blocking_allowed=SCENE_PACK_BLOCKING_ALLOWED,
    )
    assert_manifest_has_no_forbidden_tokens(manifest)
    return manifest

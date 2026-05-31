"""Matrix Script scene-segment artifact-slot skeleton — PRE-RUNTIME (PR-3).

Turns a PR-2 :class:`MatrixScriptShotPlan` into a deterministic set of
**planned** scene-segment artifact slots. A slot describes what artifact a
shot *will eventually need* — it is NOT an artifact, NOT a deliverable, and
NOT truth.

Authority:
- ``docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`` §6
  (artifact / manifest model; provider URL never deliverable; copy-into-Apollo
  rule is a later gated step).
- ``docs/contracts/factory_delivery_contract_v1.md`` (``required`` /
  ``blocking_publish`` zoning; scene_pack non-blocking).
- PR-2 shot plan (`shot_plan.py` / `shot_plan_builder.py`).

WHAT THIS MODULE IS (hard boundary — PR-3 approval):
- A frozen domain object (`MatrixScriptSceneArtifactSlot`) + a deterministic,
  pure builder (`build_scene_artifact_slots`). Planning only.

WHAT THIS MODULE IS NOT (forbidden — do NOT add here):
- NO Akool / provider / adapter import; NO live API / webhook / polling.
- NO ``artifact_storage`` call; NO file/storage write; NO ``object_exists`` /
  ``object_head``; NO upload.
- NO scene ``.mp4`` / ``final.mp4`` generation.
- NO real artifact / deliverable truth. The slot carries **expected** /
  **planned** fields only — never ``artifact_key`` / ``final_video_key`` /
  ``download_url`` / ``provider_url`` / ``temporary_url`` / ``exists`` /
  ``delivered`` / ``publish_ready`` / ``provider_task_id``.
- NO route / runtime binding; NO status-policy mutation. ``status`` is a
  static planning value (``"planned"``), never runtime state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from gateway.app.services.matrix_script.shot_plan import (
    GENERATION_MODES,
    MatrixScriptShotPlan,
    ShotPlanError,
)

# Closed planning status. Deliberately a single non-runtime value so a slot can
# never be confused with a runtime/attempt state (truth-source discipline).
SLOT_STATUS_PLANNED = "planned"
SLOT_STATUSES: frozenset = frozenset({SLOT_STATUS_PLANNED})

# Planned artifact kind for a per-shot scene segment.
EXPECTED_KIND_SCENE_SEGMENT = "scene_segment"

# Tokens that must never appear on a planned slot/manifest — these would imply
# real artifact / deliverable / provider truth. Used by the guards here and in
# ``scene_manifest.py``.
FORBIDDEN_TOKENS: Tuple[str, ...] = (
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


class SceneArtifactError(ValueError):
    """Raised when a scene artifact slot / build input is invalid."""


@dataclass(frozen=True)
class MatrixScriptSceneArtifactSlot:
    """A planned (not real) artifact slot for one shot's scene segment.

    Fields are all *expected* / *planned*. There is no key, url, existence, or
    readiness field — those are real-artifact truth, introduced only by a
    later, separately approved generation/assembly PR.
    """

    slot_id: str
    shot_id: str
    order: int
    expected_kind: str
    expected_filename: str
    generation_mode: str
    required_for_final: bool
    blocking_publish: bool
    status: str = SLOT_STATUS_PLANNED

    def __post_init__(self) -> None:
        _require_nonempty_str("slot_id", self.slot_id)
        _require_nonempty_str("shot_id", self.shot_id)
        if isinstance(self.order, bool) or not isinstance(self.order, int) or self.order < 1:
            raise SceneArtifactError("order must be an int >= 1")
        _require_nonempty_str("expected_kind", self.expected_kind)
        _require_nonempty_str("expected_filename", self.expected_filename)
        if self.generation_mode not in GENERATION_MODES:
            raise SceneArtifactError(
                f"generation_mode '{self.generation_mode}' is outside the closed set"
            )
        if not isinstance(self.required_for_final, bool):
            raise SceneArtifactError("required_for_final must be a bool")
        if not isinstance(self.blocking_publish, bool):
            raise SceneArtifactError("blocking_publish must be a bool")
        # Defensive clamp mirroring factory_delivery_contract_v1
        # (required=false ⇒ blocking_publish=false). A scene segment is an
        # intermediate artifact and is never itself a publish-blocking
        # deliverable, so blocking_publish must be False here regardless.
        if self.blocking_publish:
            raise SceneArtifactError(
                "a scene segment slot must carry blocking_publish=False "
                "(intermediate artifact; final_video is the publish deliverable)"
            )
        if self.status not in SLOT_STATUSES:
            raise SceneArtifactError(
                f"status '{self.status}' is outside the closed planning set {sorted(SLOT_STATUSES)}"
            )


def _require_nonempty_str(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SceneArtifactError(f"{name} must be a non-empty string")


def scene_slot_to_dict(slot: MatrixScriptSceneArtifactSlot) -> Dict[str, Any]:
    """Pure serialization (closed key set; no artifact-truth / provider field)."""
    return {
        "slot_id": slot.slot_id,
        "shot_id": slot.shot_id,
        "order": slot.order,
        "expected_kind": slot.expected_kind,
        "expected_filename": slot.expected_filename,
        "generation_mode": slot.generation_mode,
        "required_for_final": slot.required_for_final,
        "blocking_publish": slot.blocking_publish,
        "status": slot.status,
    }


def assert_no_forbidden_tokens(blob: str) -> None:
    """Raise ``SceneArtifactError`` if any forbidden truth/provider token leaks."""
    lowered = blob.lower()
    hits: List[str] = [tok for tok in FORBIDDEN_TOKENS if tok in lowered]
    if hits:
        raise SceneArtifactError(f"planned object leaks forbidden tokens: {hits}")


def build_scene_artifact_slots(
    plan: MatrixScriptShotPlan,
) -> Tuple[MatrixScriptSceneArtifactSlot, ...]:
    """Build one planned scene-segment slot per shot, preserving order.

    Deterministic and pure: no clock, no randomness, no I/O. ``expected_filename``
    is a planned name (``scene_001.mp4`` …), never an artifact key or URL.
    """
    if not isinstance(plan, MatrixScriptShotPlan):
        raise SceneArtifactError("plan must be a MatrixScriptShotPlan")
    if not plan.shots:
        raise SceneArtifactError("shot plan has no shots")

    slots: List[MatrixScriptSceneArtifactSlot] = []
    for shot in plan.shots:
        slots.append(
            MatrixScriptSceneArtifactSlot(
                slot_id=f"{plan.plan_id}-scene-{shot.order:02d}",
                shot_id=shot.shot_id,
                order=shot.order,
                expected_kind=EXPECTED_KIND_SCENE_SEGMENT,
                expected_filename=f"scene_{shot.order:03d}.mp4",
                generation_mode=shot.generation_mode,
                # A scene segment is required for assembling the final video,
                # but is an intermediate artifact — never a publish deliverable.
                required_for_final=bool(shot.blocking),
                blocking_publish=False,
                status=SLOT_STATUS_PLANNED,
            )
        )
    return tuple(slots)

"""Matrix Script shot-plan domain object — SKELETON ONLY (Phase 3 PR-2).

The shot plan is the Matrix Script line-internal **L2 production-line object**
that turns an accepted content structure / outline (Hook / Body / CTA) into a
deterministic ordered set of 4–8 shot specs. It is the object future
scene-segment generation, artifact binding, and FFmpeg assembly will consume.

Authority:
- ``docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`` (PR-2
  row; §5 L2 orchestration; §6 artifact/state model).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1A (Hook / Body / CTA).
- ``docs/product/matrix_script_product_flow_v2_delta.md`` (storyboard / shot
  plan as the first product object).
- ``docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md``
  (``scene_plan_binding`` storyboard intent — this skeleton models its shape
  line-internally without authoring any packet/contract binding).
- ``docs/contracts/factory_scene_plan_contract_v1.md`` /
  ``factory_content_structure_contract_v1.md`` (conceptual relation only;
  no concrete schema is changed here).

WHAT THIS MODULE IS (hard boundary — PR-2 approval):
- A small, frozen, deterministic domain model + closed business-mode set +
  validation helpers + pure serialization.

WHAT THIS MODULE IS NOT (forbidden by the PR-2 review — do NOT add here):
- NO Akool import / provider / adapter / capability-enum dependency.
- NO live API, webhook, or polling.
- NO ``final.mp4`` generation, no artifact-storage write, no artifact truth.
- NO task route / runtime binding, no task-status write.
- NO schema / packet / contract change; this is a line-internal object only.
- NO ``provider`` / ``vendor`` / ``model_id`` / ``credit`` /
  ``provider_task_id`` / ``temporary_url`` / ``final_video`` / ``artifact_key``
  field — ``generation_mode`` is an Apollo-native *business intent*, never a
  provider/model selector.

The shot plan is NOT deliverable truth. It is a pre-generation plan object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Closed set of Apollo-native generation *business modes*. These describe what
# kind of shot is intended, NOT which provider/model produces it. The L3/L4
# capability routing (and any future Akool binding) is deliberately absent.
GENERATION_MODE_STATIC_ASSET = "static_asset"
GENERATION_MODE_IMAGE_TO_VIDEO = "image_to_video"
GENERATION_MODE_AVATAR_SEGMENT = "avatar_segment"
GENERATION_MODE_BROLL = "broll"
GENERATION_MODE_TITLE_CARD = "title_card"
GENERATION_MODE_CTA_CARD = "cta_card"

GENERATION_MODES: frozenset = frozenset(
    {
        GENERATION_MODE_STATIC_ASSET,
        GENERATION_MODE_IMAGE_TO_VIDEO,
        GENERATION_MODE_AVATAR_SEGMENT,
        GENERATION_MODE_BROLL,
        GENERATION_MODE_TITLE_CARD,
        GENERATION_MODE_CTA_CARD,
    }
)

# Closed shot-plan sizing rules (Phase 3 first-experiment scope: 9:16 short,
# 20–60s, 4–8 shots per the PR-0 design §5.2).
MIN_SHOTS = 4
MAX_SHOTS = 8

# Tokens that must never appear on this domain object (operator-boundary +
# truth-source discipline). Used by ``assert_no_forbidden_tokens``.
_FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "akool",
    "provider",
    "vendor",
    "model_id",
    "credit",
    "provider_task_id",
    "temporary_url",
    "final_video",
    "artifact_key",
)


class ShotPlanError(ValueError):
    """Raised when a shot plan / spec is structurally invalid."""


@dataclass(frozen=True)
class MatrixScriptShotSpec:
    """A single shot in a Matrix Script shot plan.

    All fields are contract-shaped business intent. No provider / model /
    artifact / URL field exists by construction.
    """

    shot_id: str
    order: int
    duration_seconds: float
    role: Optional[str]
    visual_intent: str
    action: str
    scene_context: str
    asset_need: str
    audio_text: str
    subtitle_text: str
    generation_mode: str
    blocking: bool = True

    def __post_init__(self) -> None:
        _require_nonempty_str("shot_id", self.shot_id)
        if isinstance(self.order, bool) or not isinstance(self.order, int) or self.order < 1:
            raise ShotPlanError("order must be an int >= 1")
        if (
            isinstance(self.duration_seconds, bool)
            or not isinstance(self.duration_seconds, (int, float))
            or self.duration_seconds <= 0
        ):
            raise ShotPlanError("duration_seconds must be a positive number")
        if self.role is not None and not isinstance(self.role, str):
            raise ShotPlanError("role must be a string or None")
        _require_nonempty_str("visual_intent", self.visual_intent)
        _require_nonempty_str("action", self.action)
        _require_nonempty_str("scene_context", self.scene_context)
        _require_nonempty_str("asset_need", self.asset_need)
        # audio_text / subtitle_text may be empty (e.g. a silent title card),
        # but must be strings so downstream planning is total.
        if not isinstance(self.audio_text, str):
            raise ShotPlanError("audio_text must be a string")
        if not isinstance(self.subtitle_text, str):
            raise ShotPlanError("subtitle_text must be a string")
        if self.generation_mode not in GENERATION_MODES:
            raise ShotPlanError(
                f"generation_mode '{self.generation_mode}' is outside the closed "
                f"set {sorted(GENERATION_MODES)}"
            )
        if not isinstance(self.blocking, bool):
            raise ShotPlanError("blocking must be a bool")


@dataclass(frozen=True)
class MatrixScriptShotPlan:
    """An ordered 4–8 shot plan for one Matrix Script task / variant.

    The shot plan is a pre-generation L2 object — never deliverable truth and
    never an artifact handle.
    """

    plan_id: str
    task_id: Optional[str]
    aspect_ratio: str
    target_duration_seconds: float
    shots: Tuple[MatrixScriptShotSpec, ...]
    source_outline_ref: Optional[str] = None

    def __post_init__(self) -> None:
        _require_nonempty_str("plan_id", self.plan_id)
        if self.task_id is not None and not isinstance(self.task_id, str):
            raise ShotPlanError("task_id must be a string or None")
        _require_nonempty_str("aspect_ratio", self.aspect_ratio)
        if (
            isinstance(self.target_duration_seconds, bool)
            or not isinstance(self.target_duration_seconds, (int, float))
            or self.target_duration_seconds <= 0
        ):
            raise ShotPlanError("target_duration_seconds must be a positive number")
        if not isinstance(self.shots, tuple) or not self.shots:
            raise ShotPlanError("shots must be a non-empty tuple")
        for shot in self.shots:
            if not isinstance(shot, MatrixScriptShotSpec):
                raise ShotPlanError("shots must contain MatrixScriptShotSpec")
        if not MIN_SHOTS <= len(self.shots) <= MAX_SHOTS:
            raise ShotPlanError(
                f"shot count {len(self.shots)} is outside the allowed range "
                f"[{MIN_SHOTS}, {MAX_SHOTS}]"
            )
        orders = [s.order for s in self.shots]
        if orders != list(range(1, len(self.shots) + 1)):
            raise ShotPlanError("shot orders must be contiguous 1..N in sequence")
        if self.source_outline_ref is not None and not isinstance(
            self.source_outline_ref, str
        ):
            raise ShotPlanError("source_outline_ref must be a string or None")

    @property
    def total_duration_seconds(self) -> float:
        return round(sum(s.duration_seconds for s in self.shots), 3)


def _require_nonempty_str(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ShotPlanError(f"{name} must be a non-empty string")


def shot_spec_to_dict(spec: MatrixScriptShotSpec) -> Dict[str, Any]:
    """Pure serialization of a shot spec (closed key set; no provider field)."""
    return {
        "shot_id": spec.shot_id,
        "order": spec.order,
        "duration_seconds": spec.duration_seconds,
        "role": spec.role,
        "visual_intent": spec.visual_intent,
        "action": spec.action,
        "scene_context": spec.scene_context,
        "asset_need": spec.asset_need,
        "audio_text": spec.audio_text,
        "subtitle_text": spec.subtitle_text,
        "generation_mode": spec.generation_mode,
        "blocking": spec.blocking,
    }


def shot_plan_to_dict(plan: MatrixScriptShotPlan) -> Dict[str, Any]:
    """Pure serialization of a shot plan (closed key set; no provider field).

    NOTE: there is intentionally no ``final_video`` / ``artifact_key`` /
    ``deliverable`` key — the shot plan is a pre-generation plan, not truth.
    """
    return {
        "plan_id": plan.plan_id,
        "task_id": plan.task_id,
        "aspect_ratio": plan.aspect_ratio,
        "target_duration_seconds": plan.target_duration_seconds,
        "total_duration_seconds": plan.total_duration_seconds,
        "source_outline_ref": plan.source_outline_ref,
        "shots": [shot_spec_to_dict(s) for s in plan.shots],
    }


def assert_no_forbidden_tokens(plan: MatrixScriptShotPlan) -> None:
    """Defensive guard: the serialized plan carries no provider/vendor token.

    Raises ``ShotPlanError`` if any forbidden token appears anywhere in the
    serialized plan (keys or string values). This encodes the operator-boundary
    + truth-source discipline structurally rather than by convention.
    """
    blob = repr(shot_plan_to_dict(plan)).lower()
    hits: List[str] = [tok for tok in _FORBIDDEN_TOKENS if tok in blob]
    if hits:
        raise ShotPlanError(f"shot plan leaks forbidden tokens: {hits}")


def validate_shot_plan(plan: MatrixScriptShotPlan) -> MatrixScriptShotPlan:
    """Validate a fully-built shot plan and return it unchanged.

    Construction already enforces the structural invariants (count, ordering,
    closed mode set, required fields); this adds the operator-boundary token
    guard and the per-shot required-content guard so callers can assert a
    single entry point.
    """
    if not isinstance(plan, MatrixScriptShotPlan):
        raise ShotPlanError("plan must be a MatrixScriptShotPlan")
    for shot in plan.shots:
        _require_nonempty_str("visual_intent", shot.visual_intent)
        _require_nonempty_str("audio_text_or_subtitle", shot.audio_text or shot.subtitle_text)
        _require_nonempty_str("asset_need", shot.asset_need)
    assert_no_forbidden_tokens(plan)
    return plan

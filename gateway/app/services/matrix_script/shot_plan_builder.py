"""Deterministic Matrix Script shot-plan builder — SKELETON ONLY (PR-2).

Converts a Matrix Script content structure / outline (Hook / Body / CTA) into a
deterministic 4–8 shot :class:`MatrixScriptShotPlan`. Pure and side-effect-free:

- NO external API, NO Akool import, NO provider/adapter dependency.
- NO randomness (``plan_id`` is a stable content hash; no clock, no uuid).
- NO file write, NO storage write, NO task-status write, NO route/runtime
  binding.
- NO ``final.mp4`` / artifact / deliverable truth is created.

See ``shot_plan.py`` for the full hard-boundary statement. The builder is
input-agnostic about *where* the outline came from — a fixture dict, the
existing Phase B authoring result, or a future Outline Contract — so long as it
exposes Hook / Body / CTA content.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from gateway.app.services.matrix_script.shot_plan import (
    GENERATION_MODE_AVATAR_SEGMENT,
    GENERATION_MODE_BROLL,
    GENERATION_MODE_CTA_CARD,
    GENERATION_MODE_IMAGE_TO_VIDEO,
    GENERATION_MODE_STATIC_ASSET,
    MAX_SHOTS,
    MIN_SHOTS,
    MatrixScriptShotPlan,
    MatrixScriptShotSpec,
    ShotPlanError,
    validate_shot_plan,
)

_DEFAULT_ASPECT_RATIO = "9:16"
_DEFAULT_TARGET_DURATION_SECONDS = 30.0

# Number of framing shots (hook + cta) that bracket the body shots.
_FRAMING_SHOTS = 2
# Body shots therefore range in [MIN_SHOTS-2, MAX_SHOTS-2] = [2, 6].
_MIN_BODY_SHOTS = MIN_SHOTS - _FRAMING_SHOTS
_MAX_BODY_SHOTS = MAX_SHOTS - _FRAMING_SHOTS

# Deterministic body-shot mode rotation (no avatar here; avatar is reserved for
# the role-led hook so role attribution stays unambiguous).
_BODY_MODE_CYCLE: Tuple[str, ...] = (
    GENERATION_MODE_STATIC_ASSET,
    GENERATION_MODE_IMAGE_TO_VIDEO,
    GENERATION_MODE_BROLL,
)

# Deterministic asset-need wording per business mode.
_ASSET_NEED_BY_MODE: Mapping[str, str] = {
    GENERATION_MODE_AVATAR_SEGMENT: "presenter_reference_image",
    GENERATION_MODE_IMAGE_TO_VIDEO: "key_visual_still",
    GENERATION_MODE_STATIC_ASSET: "product_or_scene_still",
    GENERATION_MODE_BROLL: "broll_clip_candidate",
    GENERATION_MODE_CTA_CARD: "cta_card_template",
}


def _coerce_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalise_body(value: Any) -> List[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        out: List[str] = []
        for item in value:
            text = _coerce_str(item)
            if text:
                out.append(text)
        return out
    return []


def _plan_id(payload: Mapping[str, Any]) -> str:
    """Stable, deterministic content hash → ``shotplan-<12 hex>``.

    No clock, no uuid, no randomness: identical input always yields the same id.
    """
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
    return f"shotplan-{digest}"


def _distribute(points: List[str], buckets: int) -> List[str]:
    """Deterministically map body points onto exactly ``buckets`` shot texts.

    - More points than buckets → contiguous even chunking (joined per bucket).
    - Fewer points than buckets → cycle points, appending a deterministic facet
      marker so each shot text stays distinct and reproducible.
    """
    if buckets <= 0:
        return []
    n = len(points)
    if n == 0:
        return []
    if n >= buckets:
        # even contiguous chunking
        base, extra = divmod(n, buckets)
        result: List[str] = []
        idx = 0
        for b in range(buckets):
            size = base + (1 if b < extra else 0)
            chunk = points[idx : idx + size]
            idx += size
            result.append(" ".join(chunk))
        return result
    # fewer points than buckets: cycle with a facet marker on the wrap-arounds
    result = []
    for b in range(buckets):
        point = points[b % n]
        if b < n:
            result.append(point)
        else:
            facet = (b // n) + 1
            result.append(f"{point}（展开 {facet}）")
    return result


def _target_body_count(body_points: List[str]) -> int:
    return max(_MIN_BODY_SHOTS, min(_MAX_BODY_SHOTS, max(len(body_points), _MIN_BODY_SHOTS)))


def _even_durations(total: float, n: int) -> List[float]:
    base = round(total / n, 2)
    durations = [base] * (n - 1)
    last = round(total - base * (n - 1), 2)
    if last <= 0:
        # guard pathological rounding; fall back to an even split
        last = base
    durations.append(last)
    return durations


def build_shot_plan(
    outline: Mapping[str, Any],
    *,
    task_id: Optional[str] = None,
    aspect_ratio: str = _DEFAULT_ASPECT_RATIO,
    target_duration_seconds: float = _DEFAULT_TARGET_DURATION_SECONDS,
    source_outline_ref: Optional[str] = None,
) -> MatrixScriptShotPlan:
    """Build a deterministic 4–8 shot plan from a Hook / Body / CTA outline.

    ``outline`` accepts: ``hook`` (str), ``body`` (str | list[str]),
    ``cta`` (str), optional ``role`` (str). Raises :class:`ShotPlanError` on an
    empty / contentless outline.
    """
    if not isinstance(outline, Mapping):
        raise ShotPlanError("outline must be a mapping")

    hook = _coerce_str(outline.get("hook"))
    cta = _coerce_str(outline.get("cta"))
    body_points = _normalise_body(outline.get("body"))
    role = _coerce_str(outline.get("role")) or None

    if not hook and not cta and not body_points:
        raise ShotPlanError("outline is empty: provide at least hook / body / cta content")
    if not hook:
        raise ShotPlanError("outline.hook is required")
    if not cta:
        raise ShotPlanError("outline.cta is required")
    if not body_points:
        raise ShotPlanError("outline.body must provide at least one point")

    body_count = _target_body_count(body_points)
    body_texts = _distribute(body_points, body_count)
    total_shots = _FRAMING_SHOTS + body_count
    durations = _even_durations(float(target_duration_seconds), total_shots)

    plan_id = _plan_id(
        {
            "task_id": task_id,
            "aspect_ratio": aspect_ratio,
            "target_duration_seconds": target_duration_seconds,
            "hook": hook,
            "body": body_points,
            "cta": cta,
            "role": role,
        }
    )

    shots: List[MatrixScriptShotSpec] = []
    order = 1

    # Shot 1 — hook (role-led avatar when a role is supplied, else dynamic key visual).
    hook_mode = GENERATION_MODE_AVATAR_SEGMENT if role else GENERATION_MODE_IMAGE_TO_VIDEO
    shots.append(
        MatrixScriptShotSpec(
            shot_id=f"{plan_id}-{order:02d}",
            order=order,
            duration_seconds=durations[order - 1],
            role=role if hook_mode == GENERATION_MODE_AVATAR_SEGMENT else None,
            visual_intent="开场钩子：抓住前 3 秒注意力",
            action="present_hook",
            scene_context="hook",
            asset_need=_ASSET_NEED_BY_MODE[hook_mode],
            audio_text=hook,
            subtitle_text=hook,
            generation_mode=hook_mode,
            blocking=True,
        )
    )
    order += 1

    # Body shots.
    for i, text in enumerate(body_texts):
        mode = _BODY_MODE_CYCLE[i % len(_BODY_MODE_CYCLE)]
        shots.append(
            MatrixScriptShotSpec(
                shot_id=f"{plan_id}-{order:02d}",
                order=order,
                duration_seconds=durations[order - 1],
                role=None,
                visual_intent=f"主体段 {i + 1}：展示 / 过程 / 对比",
                action="present_body_point",
                scene_context="body",
                asset_need=_ASSET_NEED_BY_MODE[mode],
                audio_text=text,
                subtitle_text=text,
                generation_mode=mode,
                blocking=True,
            )
        )
        order += 1

    # Final shot — CTA card.
    shots.append(
        MatrixScriptShotSpec(
            shot_id=f"{plan_id}-{order:02d}",
            order=order,
            duration_seconds=durations[order - 1],
            role=None,
            visual_intent="结尾引导：评论 / 私信 / 点击",
            action="present_cta",
            scene_context="cta",
            asset_need=_ASSET_NEED_BY_MODE[GENERATION_MODE_CTA_CARD],
            audio_text=cta,
            subtitle_text=cta,
            generation_mode=GENERATION_MODE_CTA_CARD,
            blocking=True,
        )
    )

    plan = MatrixScriptShotPlan(
        plan_id=plan_id,
        task_id=task_id,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=float(target_duration_seconds),
        shots=tuple(shots),
        source_outline_ref=source_outline_ref,
    )
    return validate_shot_plan(plan)

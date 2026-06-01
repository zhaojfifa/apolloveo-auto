"""Matrix Script Tomato Real Result — operator acceptance gate (PR-A, L3).

Pure derivation of the L3 readiness fields from per-shot render facts. This is
the boundary the baseline §7 binds: technical success (a playable final.mp4) is
NOT operator success. A fallback-only / color-card result MUST fail operator
acceptance and MUST NOT become a delivery candidate.

No I/O, no provider name, no contract/schema change. Inputs are plain facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

# visual_semantic_match closed values (operator-facing).
MATCH_PASS = "pass"
MATCH_PARTIAL = "partial_pass"
MATCH_FAILED = "failed"

# Minimum bar (baseline §7.2): ≥1 real visual shot AND ≥3 semantic matches.
MIN_REAL_VISUAL = 1
MIN_SHOT_MATCH = 3

BLOCKED_FALLBACK_ONLY = "fallback_only_or_missing_real_visuals"


@dataclass(frozen=True)
class ShotRenderFact:
    """What actually happened for one shot during the controlled run."""

    shot_id: str
    source: str
    rendered: bool
    real_visual: bool
    semantic_match: bool


@dataclass(frozen=True)
class TomatoAcceptance:
    technical_preview: bool
    operator_usable: bool
    delivery_candidate: bool
    official_publish_ready: bool
    visual_semantic_match: str
    shot_count: int
    shot_match_count: int
    real_visual_count: int
    blocked_reason: Optional[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "technical_preview": self.technical_preview,
            "operator_usable": self.operator_usable,
            "delivery_candidate": self.delivery_candidate,
            "official_publish_ready": self.official_publish_ready,
            "visual_semantic_match": self.visual_semantic_match,
            "shot_count": self.shot_count,
            "shot_match_count": self.shot_match_count,
            "real_visual_count": self.real_visual_count,
            "blocked_reason": self.blocked_reason,
        }


def _classify(real_visual_count: int, shot_match_count: int, shot_count: int) -> str:
    if real_visual_count <= 0:
        return MATCH_FAILED
    if shot_count > 0 and shot_match_count >= shot_count:
        return MATCH_PASS
    if shot_match_count >= MIN_SHOT_MATCH:
        return MATCH_PARTIAL
    if shot_match_count >= 1:
        return MATCH_PARTIAL
    return MATCH_FAILED


def compute_tomato_acceptance(facts: Sequence[ShotRenderFact]) -> TomatoAcceptance:
    """Derive the L3 acceptance verdict from per-shot render facts.

    Rules (baseline §7):
    - a real local image counts as a real visual; semantic reuse does not.
    - a color-card / text-only / un-rendered shot counts for nothing.
    - operator_usable requires ≥1 real visual AND ≥3 semantic matches.
    - fallback-only → technical_preview=true, operator_usable=false, blocked.
    - official_publish_ready is always false.
    """
    rendered = [f for f in facts if f.rendered]
    shot_count = len(rendered)
    real_visual_count = sum(1 for f in rendered if f.real_visual)
    shot_match_count = sum(1 for f in rendered if f.semantic_match)

    operator_usable = real_visual_count >= MIN_REAL_VISUAL and shot_match_count >= MIN_SHOT_MATCH
    visual_semantic_match = _classify(real_visual_count, shot_match_count, shot_count)
    blocked_reason: Optional[str] = None if operator_usable else BLOCKED_FALLBACK_ONLY

    return TomatoAcceptance(
        technical_preview=not operator_usable,
        operator_usable=operator_usable,
        delivery_candidate=operator_usable,
        official_publish_ready=False,
        visual_semantic_match=visual_semantic_match,
        shot_count=shot_count,
        shot_match_count=shot_match_count,
        real_visual_count=real_visual_count,
        blocked_reason=blocked_reason,
    )


def fallback_only_acceptance(shot_count: int = 0) -> TomatoAcceptance:
    """Explicit fallback-only verdict (no real visuals at all)."""
    return TomatoAcceptance(
        technical_preview=True,
        operator_usable=False,
        delivery_candidate=False,
        official_publish_ready=False,
        visual_semantic_match=MATCH_FAILED,
        shot_count=shot_count,
        shot_match_count=0,
        real_visual_count=0,
        blocked_reason=BLOCKED_FALLBACK_ONLY,
    )

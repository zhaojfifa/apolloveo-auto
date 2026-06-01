"""Matrix Script minimal-result execution trace (PR-14R, Operator Visibility).

Canonical, closed step list for the synchronous minimal-result loop, plus a
pure builder that derives a per-step status from a result surface dict. This is
the "process observable" axis: operators see what the loop did, not vendor or
provider internals.

v1 is synchronous (no async progress): a present local result ⇒ all steps
``done``; absence ⇒ ``pending``. No Akool / provider / vendor / model / credit;
no publish or storage truth.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

# Closed, ordered step set (step_id, operator label). Mirrors the loop:
# shot plan → scene clips → audio → subtitles → assembly → surface.
TRACE_STEPS = (
    ("shot_plan", "生成镜头计划"),
    ("scene_clips", "生成场景片段"),
    ("audio", "生成音频"),
    ("subtitles", "生成字幕"),
    ("assembly", "合成成片"),
    ("surface", "生成结果视图"),
)

STATUS_DONE = "done"
STATUS_PENDING = "pending"
STATUS_FAILED = "failed"
TRACE_STATUSES = frozenset({STATUS_DONE, STATUS_PENDING, STATUS_FAILED})

_FORBIDDEN_TOKENS = (
    "akool", "provider", "vendor", "model_id", "credit",
    "provider_url", "download_url", "artifact_key", "r2_key",
    "publish_url", "publish_status",
)


def build_minimal_result_trace(
    surface: Optional[Mapping[str, Any]],
) -> List[Dict[str, str]]:
    """Build the closed 6-step trace; all ``done`` when a local result exists.

    ``surface`` is the PR-8R surface-view dict (or its workbench-block form).
    When ``has_result`` is truthy every step is ``done`` (synchronous loop
    completed); otherwise every step is ``pending``.
    """
    has_result = bool(surface.get("has_result")) if isinstance(surface, Mapping) else False
    status = STATUS_DONE if has_result else STATUS_PENDING
    return [
        {"step": step_id, "label": label, "status": status}
        for step_id, label in TRACE_STEPS
    ]


def trace_step_labels() -> List[str]:
    """Ordered operator labels (for template/parity tests)."""
    return [label for _, label in TRACE_STEPS]


def assert_no_trace_forbidden_tokens(payload: object) -> None:
    blob = str(payload).lower()
    hits = [t for t in _FORBIDDEN_TOKENS if t in blob]
    if hits:
        raise ValueError(f"trace leaks forbidden tokens: {hits}")

"""Declarative Ready Gate Engine (TASK-2.3).

Provides typed dataclasses for declaring readiness rules and a pure-function
evaluator that produces the ``ready_gate`` dict consumed by the workbench UI.

Four-pass evaluation:
  1. Signal extraction — named booleans from task/state
  2. Override application — artifact-presence overrides flags
  3. Gate evaluation — composite readiness from signals
  4. Blocking collection — human-readable blockers
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


# ---------------------------------------------------------------------------
# Rule dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Signal:
    """A named boolean fact extracted from task/state data."""

    name: str
    extract: Callable[[dict, dict], bool]
    reason_key: str | None = None
    reason_extract: Callable[[dict, dict], str] | None = None


@dataclass(frozen=True)
class OverrideRule:
    """When *evidence_signal* is True, force *target_signal* to *force_value*."""

    evidence_signal: str
    target_signal: str
    force_value: bool = False


@dataclass(frozen=True)
class GateRule:
    """A readiness gate: ``all(requires) AND (len(unless)==0 OR any(unless))``.

    *requires* are signal/gate names that must ALL be True.
    *unless* are signal names where at least ONE must be True (OR bypass).
    If *unless* is empty the OR clause is skipped (always passes).
    """

    name: str
    requires: tuple[str, ...]
    unless: tuple[str, ...] = ()


@dataclass(frozen=True)
class BlockingRule:
    """Emit a blocking reason when a gate is unmet.

    *when_missing*: the signal that must be False to trigger.
      Use ``"__always__"`` to always trigger when the parent gate is False.
    *unless_signal*: skip this rule if this signal is True.
    *extra_requires*: additional signals that must ALL be True for this rule to fire.
    *reason_from*: if set, read the reason string from ``reasons[reason_from]``
      instead of using the static *reason* field.
    """

    reason: str
    when_missing: str
    unless_signal: str | None = None
    extra_requires: tuple[str, ...] = ()
    reason_from: str | None = None
    parent_gate: str = "compose_ready"


@dataclass(frozen=True)
class ReadyGateSpec:
    """Complete ready-gate rule set for one production line."""

    line_id: str
    signals: tuple[Signal, ...]
    overrides: tuple[OverrideRule, ...] = ()
    gates: tuple[GateRule, ...] = ()
    blocking: tuple[BlockingRule, ...] = ()


# ---------------------------------------------------------------------------
# Evaluation engine
# ---------------------------------------------------------------------------


def evaluate_ready_gate(
    spec: ReadyGateSpec,
    task: Dict[str, Any],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate all rules and return the ``ready_gate`` dict.

    This is a **pure function** — it reads *task* and *state* but never
    mutates them.  The returned dict has the same 9-field shape that the
    workbench frontend expects.
    """

    # ── Pass 1: Signal extraction ─────────────────────────────────────────
    signals: dict[str, bool] = {}
    reasons: dict[str, str] = {}

    for sig in spec.signals:
        signals[sig.name] = sig.extract(task, state)
        if sig.reason_key and sig.reason_extract:
            reasons[sig.reason_key] = sig.reason_extract(task, state)

    # ── Pass 2: Override application ──────────────────────────────────────
    for ov in spec.overrides:
        if signals.get(ov.evidence_signal, False):
            signals[ov.target_signal] = ov.force_value

    # ── Pass 3: Gate evaluation ───────────────────────────────────────────
    gates: dict[str, bool] = {}

    for gate in spec.gates:
        # Resolve requires from signals OR previously computed gates
        requires_met = all(
            signals.get(r, gates.get(r, False)) for r in gate.requires
        )
        if gate.unless:
            unless_met = any(signals.get(u, False) for u in gate.unless)
        else:
            unless_met = True  # no unless clause = always passes
        gates[gate.name] = requires_met and unless_met

    # ── Pass 4: Blocking collection ───────────────────────────────────────
    blocking: list[str] = []

    for br in spec.blocking:
        # Only emit when parent gate is False
        if gates.get(br.parent_gate, False):
            continue
        # Check when_missing condition
        if br.when_missing != "__always__" and signals.get(br.when_missing, False):
            continue
        # Check unless_signal
        if br.unless_signal and signals.get(br.unless_signal, False):
            continue
        # Check extra_requires
        if br.extra_requires and not all(signals.get(r, False) for r in br.extra_requires):
            continue
        # Resolve reason string
        reason = br.reason
        if br.reason_from:
            reason = reasons.get(br.reason_from, "")
        if reason:
            blocking.append(reason)

    # ── Post-process: compose_reason ──────────────────────────────────────
    compose_ready = gates.get("compose_ready", False)
    stale_reason = str(
        state.get("final_stale_reason")
        or state.get("composed_reason")
        or ""
    ).strip()
    if compose_ready:
        compose_reason = "ready"
    elif stale_reason in {"final_stale_after_dub", "final_stale_after_subtitles"}:
        compose_reason = stale_reason
    elif (
        signals.get("no_dub", False)
        and not signals.get("subtitle_ready", False)
        and reasons.get("no_dub_reason")
    ):
        compose_reason = reasons["no_dub_reason"]
    else:
        compose_reason = "compose_not_done"

    # ── Build output dict (9 fields, format-compatible) ───────────────────
    audio = state.get("audio") if isinstance(state.get("audio"), dict) else {}
    subtitle_ready = signals.get("subtitle_ready", False)
    audio_ready = signals.get("audio_ready", False)

    return {
        "final_exists": signals.get("final_exists", False),
        "subtitle_ready": subtitle_ready,
        "subtitle_ready_reason": reasons.get(
            "subtitle_ready_reason", "ready" if subtitle_ready else "subtitle_missing"
        ),
        "audio_ready": audio_ready,
        "audio_ready_reason": reasons.get(
            "audio_ready_reason",
            str(audio.get("audio_ready_reason") or ("ready" if audio_ready else "audio_not_ready")),
        ),
        "compose_ready": compose_ready,
        "publish_ready": gates.get("publish_ready", compose_ready),
        "compose_reason": compose_reason,
        "blocking": blocking,
    }

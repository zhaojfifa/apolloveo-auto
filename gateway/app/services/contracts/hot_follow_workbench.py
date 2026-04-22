from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _CompatModel(BaseModel):
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class PipelineStepStatus(_CompatModel):
    """L1 pipeline step status only; no business readiness interpretation."""

    key: str
    status: str
    state: str | None = None
    label: str | None = None
    updated_at: Any = None
    error: Any = None
    message: Any = None


class ArtifactFacts(_CompatModel):
    """L2 artifact facts: physical/resolved artifact truth and route input facts."""

    raw_exists: bool | None = None
    subtitle_exists: bool | None = None
    audio_exists: bool | None = None
    final_exists: bool | None = None
    pack_exists: bool | None = None
    compose_input: dict[str, Any] | None = None
    audio_lane: dict[str, Any] | None = None
    helper_translate_failed: bool | None = None
    helper_translate_failed_voice_led: bool | None = None


class CurrentAttemptState(_CompatModel):
    """L3 runtime resolution derived from L1/L2 and current input snapshots."""

    dub_current: bool | None = None
    audio_ready: bool | None = None
    compose_status: str | None = None
    compose_reason: str | None = None
    requires_redub: bool | None = None
    requires_recompose: bool | None = None
    current_subtitle_source: str | None = None


class ReadyGateState(_CompatModel):
    """L4 ready gate decision. It consumes L2/L3 and must not write truth."""

    compose_ready: bool
    publish_ready: bool
    blocking: list[Any] = Field(default_factory=list)
    subtitle_ready: bool | None = None
    audio_ready: bool | None = None
    compose_reason: str | None = None
    publish_reason: str | None = None


class OperatorSummaryState(_CompatModel):
    """L4 operator-facing summary derived from frozen state layers."""

    recommended_next_action: Any = None
    status: str | None = None
    message: Any = None


class AdvisoryState(_CompatModel):
    """L4 read-only advisory output from the skills/presenter boundary."""

    id: str | None = None
    decision_key: str | None = None
    recommended_next_action: str | None = None
    explanation: str | None = None
    evidence: dict[str, Any] | None = None


class PresentationState(_CompatModel):
    """L4 UI projection state. This is display-only."""

    last_successful_output: dict[str, Any] | None = None
    current_attempt: dict[str, Any] | None = None


class DeliverableItem(_CompatModel):
    """Deliverable projection row derived from artifact facts and readiness."""

    kind: str
    status: str | None = None
    state: str | None = None
    url: str | None = None
    historical: bool | None = None


class HotFollowWorkbenchResponse(_CompatModel):
    """Typed Hot Follow workbench hub response.

    This model intentionally preserves wire compatibility with the current
    workbench payload by allowing extra fields. It freezes the required
    four-layer sections so presenter code cannot silently drop the layer
    contract while retaining legacy fields during reconstruction.
    """

    task_id: str
    kind: str
    line: dict[str, Any]
    pipeline: list[PipelineStepStatus]
    subtitles: dict[str, Any]
    audio: dict[str, Any]
    compose: dict[str, Any]
    deliverables: list[DeliverableItem]
    artifact_facts: ArtifactFacts
    current_attempt: CurrentAttemptState
    ready_gate: ReadyGateState
    operator_summary: OperatorSummaryState
    presentation: PresentationState | None = None
    advisory: AdvisoryState | None = None


def validate_hot_follow_workbench_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the current wire payload without changing its shape."""

    HotFollowWorkbenchResponse.model_validate(payload)
    return payload

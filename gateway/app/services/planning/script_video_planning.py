from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from gateway.app.services.planning.prompt_registry import (
    SCRIPT_VIDEO_PROMPT_REGISTRY_REF,
    PlanningPromptRegistry,
    load_planning_prompt_registry,
)


SCRIPT_VIDEO_LINE_ID = "script_video_line"


class PlanningDraftStatus(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CandidateAssetStatus(str, Enum):
    SUGGESTED = "suggested"
    REVIEWING = "reviewing"
    REJECTED = "rejected"


class LinkedAssetStatus(str, Enum):
    LINKED = "linked"
    SUPERSEDED = "superseded"
    DETACHED = "detached"


@dataclass(frozen=True)
class SegmentDraft:
    segment_id: str
    source_text: str
    narrative_role: str
    timing_hint: str | None
    prompt_template_ref: str | None


@dataclass(frozen=True)
class ShotUnitDraft:
    shot_id: str
    segment_id: str
    shot_text: str
    shot_intent: str
    camera_hint: str | None
    location_hint: str | None
    required_roles: tuple[str, ...]
    required_props: tuple[str, ...]
    candidate_asset_refs: tuple[str, ...]
    linked_asset_refs: tuple[str, ...]
    prompt_template_ref: str | None


@dataclass(frozen=True)
class ExtractedPlanningEntity:
    entity_id: str
    entity_type: str
    name: str
    source: str
    confidence: float
    segment_ids: tuple[str, ...]
    shot_ids: tuple[str, ...]


@dataclass(frozen=True)
class PlanningAssetCandidate:
    candidate_id: str
    asset_type: str
    label: str
    source: str
    confidence: float
    evidence: tuple[str, ...]
    status: CandidateAssetStatus
    scope_type: str
    scope_id: str
    asset_ref: str | None = None


@dataclass(frozen=True)
class PlanningAssetLink:
    link_id: str
    asset_ref: str
    asset_type: str
    scope_type: str
    scope_id: str
    linked_from_candidate_id: str | None
    accepted_by: str | None
    accepted_at: str | None
    usage_scope: str
    status: LinkedAssetStatus


@dataclass(frozen=True)
class PlanningUsageRecord:
    usage_id: str
    line_id: str
    planning_id: str
    run_ref: str | None
    step_id: str
    scope_type: str
    scope_id: str
    asset_ref: str
    usage_role: str
    source_state: str
    source_id: str | None = None


@dataclass(frozen=True)
class ScriptVideoPlanningDraft:
    planning_id: str
    line_id: str
    source_ref: str
    run_ref: str | None
    status: PlanningDraftStatus
    script_input: str
    prompt_template_registry_ref: str
    prompt_category: str
    prompt_family: str
    prompt_template_ref: str | None
    segments: tuple[SegmentDraft, ...]
    shots: tuple[ShotUnitDraft, ...]
    extracted_entities: tuple[ExtractedPlanningEntity, ...]
    candidate_assets: tuple[PlanningAssetCandidate, ...]
    linked_assets: tuple[PlanningAssetLink, ...]
    file_usage_index: tuple[PlanningUsageRecord, ...]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_blocks(script_input: str) -> list[str]:
    blocks = [block.strip() for block in str(script_input or "").replace("\r\n", "\n").split("\n\n")]
    blocks = [block for block in blocks if block]
    if blocks:
        return blocks
    single = str(script_input or "").strip()
    return [single] if single else []


def _entity_type_hint_group(entity_hints: dict[str, list[str]] | None, key: str) -> list[str]:
    if not isinstance(entity_hints, dict):
        return []
    values = entity_hints.get(key) or []
    return [str(value or "").strip() for value in values if str(value or "").strip()]


class ScriptVideoPlanningService:
    def __init__(self, *, prompt_registry: PlanningPromptRegistry | None = None) -> None:
        self._prompt_registry = prompt_registry or load_planning_prompt_registry()

    def create_draft(
        self,
        *,
        planning_id: str,
        source_ref: str,
        script_input: str,
        run_ref: str | None = None,
        entity_hints: dict[str, list[str]] | None = None,
        prompt_category: str = "shot_planning",
        prompt_family: str = "story_beats",
    ) -> ScriptVideoPlanningDraft:
        template = self._prompt_registry.resolve_default(category=prompt_category, family=prompt_family)
        segments: list[SegmentDraft] = []
        shots: list[ShotUnitDraft] = []
        blocks = _normalized_blocks(script_input)
        for idx, block in enumerate(blocks, start=1):
            segment_id = f"segment-{idx}"
            shot_id = f"shot-{idx}"
            segment = SegmentDraft(
                segment_id=segment_id,
                source_text=block,
                narrative_role="story_beat",
                timing_hint=None,
                prompt_template_ref=template.template_id if template else None,
            )
            shot = ShotUnitDraft(
                shot_id=shot_id,
                segment_id=segment_id,
                shot_text=block,
                shot_intent="story_beat",
                camera_hint="medium",
                location_hint=None,
                required_roles=tuple(_entity_type_hint_group(entity_hints, "roles")),
                required_props=tuple(_entity_type_hint_group(entity_hints, "props")),
                candidate_asset_refs=(),
                linked_asset_refs=(),
                prompt_template_ref=template.template_id if template else None,
            )
            segments.append(segment)
            shots.append(shot)

        extracted_entities = self._build_entities(entity_hints, tuple(segments), tuple(shots))
        draft = ScriptVideoPlanningDraft(
            planning_id=planning_id,
            line_id=SCRIPT_VIDEO_LINE_ID,
            source_ref=source_ref,
            run_ref=run_ref,
            status=PlanningDraftStatus.DRAFT,
            script_input=str(script_input or ""),
            prompt_template_registry_ref=self._prompt_registry.registry_ref,
            prompt_category=prompt_category,
            prompt_family=prompt_family,
            prompt_template_ref=template.template_id if template else None,
            segments=tuple(segments),
            shots=tuple(shots),
            extracted_entities=extracted_entities,
            candidate_assets=(),
            linked_assets=(),
            file_usage_index=(),
        )
        return self.rebuild_usage_index(draft)

    def add_candidate_asset(
        self,
        draft: ScriptVideoPlanningDraft,
        *,
        asset_type: str,
        label: str,
        source: str,
        scope_type: str,
        scope_id: str,
        asset_ref: str | None = None,
        confidence: float = 0.5,
        evidence: list[str] | tuple[str, ...] | None = None,
    ) -> ScriptVideoPlanningDraft:
        candidate = PlanningAssetCandidate(
            candidate_id=f"cand-{uuid4().hex[:10]}",
            asset_type=str(asset_type or "").strip(),
            label=str(label or "").strip(),
            source=str(source or "").strip() or "planning",
            confidence=max(0.0, min(1.0, float(confidence))),
            evidence=tuple(str(item or "").strip() for item in (evidence or []) if str(item or "").strip()),
            status=CandidateAssetStatus.SUGGESTED,
            scope_type=str(scope_type or "").strip(),
            scope_id=str(scope_id or "").strip(),
            asset_ref=str(asset_ref or "").strip() or None,
        )
        updated = replace(
            draft,
            candidate_assets=tuple(list(draft.candidate_assets) + [candidate]),
            shots=self._attach_asset_ref_to_shots(
                draft.shots,
                candidate.scope_type,
                candidate.scope_id,
                candidate_ref=candidate.candidate_id,
                linked_ref=None,
            ),
        )
        return self.rebuild_usage_index(updated)

    def link_candidate_asset(
        self,
        draft: ScriptVideoPlanningDraft,
        *,
        candidate_id: str,
        asset_ref: str,
        accepted_by: str,
        usage_scope: str = "shot",
    ) -> ScriptVideoPlanningDraft:
        candidate = next((item for item in draft.candidate_assets if item.candidate_id == candidate_id), None)
        if candidate is None:
            raise KeyError(f"candidate not found: {candidate_id}")
        linked = PlanningAssetLink(
            link_id=f"link-{uuid4().hex[:10]}",
            asset_ref=str(asset_ref or "").strip(),
            asset_type=candidate.asset_type,
            scope_type=candidate.scope_type,
            scope_id=candidate.scope_id,
            linked_from_candidate_id=candidate.candidate_id,
            accepted_by=str(accepted_by or "").strip() or None,
            accepted_at=_utcnow_iso(),
            usage_scope=str(usage_scope or "").strip() or candidate.scope_type,
            status=LinkedAssetStatus.LINKED,
        )
        updated = replace(
            draft,
            linked_assets=tuple(list(draft.linked_assets) + [linked]),
            shots=self._attach_asset_ref_to_shots(
                draft.shots,
                linked.scope_type,
                linked.scope_id,
                candidate_ref=None,
                linked_ref=linked.link_id,
            ),
        )
        return self.rebuild_usage_index(updated)

    def rebuild_usage_index(self, draft: ScriptVideoPlanningDraft) -> ScriptVideoPlanningDraft:
        usage_records: list[PlanningUsageRecord] = []
        for segment in draft.segments:
            if segment.prompt_template_ref:
                usage_records.append(
                    PlanningUsageRecord(
                        usage_id=f"usage-{uuid4().hex[:10]}",
                        line_id=draft.line_id,
                        planning_id=draft.planning_id,
                        run_ref=draft.run_ref,
                        step_id="planning",
                        scope_type="segment",
                        scope_id=segment.segment_id,
                        asset_ref=segment.prompt_template_ref,
                        usage_role="prompt_input",
                        source_state="registry",
                        source_id=segment.prompt_template_ref,
                    )
                )
        for candidate in draft.candidate_assets:
            if candidate.asset_ref:
                usage_records.append(
                    PlanningUsageRecord(
                        usage_id=f"usage-{uuid4().hex[:10]}",
                        line_id=draft.line_id,
                        planning_id=draft.planning_id,
                        run_ref=draft.run_ref,
                        step_id="planning",
                        scope_type=candidate.scope_type,
                        scope_id=candidate.scope_id,
                        asset_ref=candidate.asset_ref,
                        usage_role="candidate",
                        source_state="candidate",
                        source_id=candidate.candidate_id,
                    )
                )
        for linked in draft.linked_assets:
            usage_records.append(
                PlanningUsageRecord(
                    usage_id=f"usage-{uuid4().hex[:10]}",
                    line_id=draft.line_id,
                    planning_id=draft.planning_id,
                    run_ref=draft.run_ref,
                    step_id="planning",
                    scope_type=linked.scope_type,
                    scope_id=linked.scope_id,
                    asset_ref=linked.asset_ref,
                    usage_role="linked",
                    source_state="linked",
                    source_id=linked.link_id,
                )
            )
        return replace(draft, file_usage_index=tuple(usage_records))

    @staticmethod
    def _attach_asset_ref_to_shots(
        shots: tuple[ShotUnitDraft, ...],
        scope_type: str,
        scope_id: str,
        *,
        candidate_ref: str | None,
        linked_ref: str | None,
    ) -> tuple[ShotUnitDraft, ...]:
        if scope_type != "shot":
            return shots
        updated: list[ShotUnitDraft] = []
        for shot in shots:
            if shot.shot_id != scope_id:
                updated.append(shot)
                continue
            candidate_refs = list(shot.candidate_asset_refs)
            linked_refs = list(shot.linked_asset_refs)
            if candidate_ref and candidate_ref not in candidate_refs:
                candidate_refs.append(candidate_ref)
            if linked_ref and linked_ref not in linked_refs:
                linked_refs.append(linked_ref)
            updated.append(
                replace(
                    shot,
                    candidate_asset_refs=tuple(candidate_refs),
                    linked_asset_refs=tuple(linked_refs),
                )
            )
        return tuple(updated)

    @staticmethod
    def _build_entities(
        entity_hints: dict[str, list[str]] | None,
        segments: tuple[SegmentDraft, ...],
        shots: tuple[ShotUnitDraft, ...],
    ) -> tuple[ExtractedPlanningEntity, ...]:
        entities: list[ExtractedPlanningEntity] = []
        segment_ids = tuple(segment.segment_id for segment in segments)
        shot_ids = tuple(shot.shot_id for shot in shots)
        for entity_type in ("roles", "scenes", "props"):
            names = _entity_type_hint_group(entity_hints, entity_type)
            normalized_type = entity_type[:-1] if entity_type.endswith("s") else entity_type
            for idx, name in enumerate(names, start=1):
                entities.append(
                    ExtractedPlanningEntity(
                        entity_id=f"{normalized_type}-{idx}",
                        entity_type=normalized_type,
                        name=name,
                        source="hint",
                        confidence=1.0,
                        segment_ids=segment_ids,
                        shot_ids=shot_ids,
                    )
                )
        return tuple(entities)

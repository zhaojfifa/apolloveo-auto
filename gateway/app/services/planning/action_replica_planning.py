from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from gateway.app.services.planning.script_video_planning import (
    CandidateAssetStatus,
    LinkedAssetStatus,
    PlanningAssetCandidate,
    PlanningAssetLink,
    PlanningDraftStatus,
    PlanningUsageRecord,
)


ACTION_REPLICA_LINE_ID = "action_replica_line"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PlanningBindingStatus(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    CONFIRMED = "confirmed"
    DETACHED = "detached"


@dataclass(frozen=True)
class ReplicaIdentity:
    replica_id: str
    display_name: str
    persona_notes: str
    identity_asset_candidate_refs: tuple[str, ...]
    identity_asset_link_refs: tuple[str, ...]


@dataclass(frozen=True)
class Wardrobe:
    wardrobe_id: str
    replica_id: str
    look_label: str
    style_notes: str
    asset_candidate_refs: tuple[str, ...]
    asset_link_refs: tuple[str, ...]


@dataclass(frozen=True)
class HandProp:
    prop_id: str
    display_name: str
    usage_notes: str
    asset_candidate_refs: tuple[str, ...]
    asset_link_refs: tuple[str, ...]


@dataclass(frozen=True)
class RoleBinding:
    role_binding_id: str
    role_name: str
    replica_id: str
    wardrobe_id: str | None
    default_prop_ids: tuple[str, ...]
    status: PlanningBindingStatus


@dataclass(frozen=True)
class ShotBinding:
    shot_binding_id: str
    shot_id: str
    role_binding_ids: tuple[str, ...]
    prop_ids: tuple[str, ...]
    camera_action_hint: str | None
    motion_hint: str | None
    candidate_asset_refs: tuple[str, ...]
    linked_asset_refs: tuple[str, ...]


@dataclass(frozen=True)
class ActionReplicaExecutionNeed:
    need_id: str
    line_id: str
    planning_id: str
    need_kind: str
    scope_type: str
    scope_id: str
    role_binding_id: str | None
    shot_binding_id: str | None
    asset_refs: tuple[str, ...]
    source_state: str


@dataclass(frozen=True)
class ActionReplicaPlanningView:
    planning_id: str
    line_id: str
    source_ref: str
    run_ref: str | None
    status: PlanningDraftStatus
    identities: tuple[ReplicaIdentity, ...]
    wardrobes: tuple[Wardrobe, ...]
    hand_props: tuple[HandProp, ...]
    role_bindings: tuple[RoleBinding, ...]
    shot_bindings: tuple[ShotBinding, ...]
    candidate_assets: tuple[PlanningAssetCandidate, ...]
    linked_assets: tuple[PlanningAssetLink, ...]
    file_usage_index: tuple[PlanningUsageRecord, ...]


class ActionReplicaPlanningService:
    def create_view(
        self,
        *,
        planning_id: str,
        source_ref: str,
        run_ref: str | None = None,
    ) -> ActionReplicaPlanningView:
        return ActionReplicaPlanningView(
            planning_id=planning_id,
            line_id=ACTION_REPLICA_LINE_ID,
            source_ref=str(source_ref or "").strip(),
            run_ref=run_ref,
            status=PlanningDraftStatus.DRAFT,
            identities=(),
            wardrobes=(),
            hand_props=(),
            role_bindings=(),
            shot_bindings=(),
            candidate_assets=(),
            linked_assets=(),
            file_usage_index=(),
        )

    def add_replica_identity(
        self,
        view: ActionReplicaPlanningView,
        *,
        display_name: str,
        persona_notes: str = "",
    ) -> ActionReplicaPlanningView:
        identity = ReplicaIdentity(
            replica_id=f"replica-{uuid4().hex[:10]}",
            display_name=str(display_name or "").strip(),
            persona_notes=str(persona_notes or "").strip(),
            identity_asset_candidate_refs=(),
            identity_asset_link_refs=(),
        )
        return replace(view, identities=tuple(list(view.identities) + [identity]))

    def add_wardrobe(
        self,
        view: ActionReplicaPlanningView,
        *,
        replica_id: str,
        look_label: str,
        style_notes: str = "",
    ) -> ActionReplicaPlanningView:
        wardrobe = Wardrobe(
            wardrobe_id=f"wardrobe-{uuid4().hex[:10]}",
            replica_id=str(replica_id or "").strip(),
            look_label=str(look_label or "").strip(),
            style_notes=str(style_notes or "").strip(),
            asset_candidate_refs=(),
            asset_link_refs=(),
        )
        return replace(view, wardrobes=tuple(list(view.wardrobes) + [wardrobe]))

    def add_hand_prop(
        self,
        view: ActionReplicaPlanningView,
        *,
        display_name: str,
        usage_notes: str = "",
    ) -> ActionReplicaPlanningView:
        hand_prop = HandProp(
            prop_id=f"prop-{uuid4().hex[:10]}",
            display_name=str(display_name or "").strip(),
            usage_notes=str(usage_notes or "").strip(),
            asset_candidate_refs=(),
            asset_link_refs=(),
        )
        return replace(view, hand_props=tuple(list(view.hand_props) + [hand_prop]))

    def bind_role(
        self,
        view: ActionReplicaPlanningView,
        *,
        role_name: str,
        replica_id: str,
        wardrobe_id: str | None = None,
        default_prop_ids: tuple[str, ...] | list[str] | None = None,
    ) -> ActionReplicaPlanningView:
        role_binding = RoleBinding(
            role_binding_id=f"role-{uuid4().hex[:10]}",
            role_name=str(role_name or "").strip(),
            replica_id=str(replica_id or "").strip(),
            wardrobe_id=str(wardrobe_id or "").strip() or None,
            default_prop_ids=tuple(str(item or "").strip() for item in (default_prop_ids or []) if str(item or "").strip()),
            status=PlanningBindingStatus.DRAFT,
        )
        return replace(view, role_bindings=tuple(list(view.role_bindings) + [role_binding]))

    def bind_shot(
        self,
        view: ActionReplicaPlanningView,
        *,
        shot_id: str,
        role_binding_ids: tuple[str, ...] | list[str],
        prop_ids: tuple[str, ...] | list[str] | None = None,
        camera_action_hint: str | None = None,
        motion_hint: str | None = None,
    ) -> ActionReplicaPlanningView:
        shot_binding = ShotBinding(
            shot_binding_id=f"shotbind-{uuid4().hex[:10]}",
            shot_id=str(shot_id or "").strip(),
            role_binding_ids=tuple(str(item or "").strip() for item in role_binding_ids if str(item or "").strip()),
            prop_ids=tuple(str(item or "").strip() for item in (prop_ids or []) if str(item or "").strip()),
            camera_action_hint=str(camera_action_hint or "").strip() or None,
            motion_hint=str(motion_hint or "").strip() or None,
            candidate_asset_refs=(),
            linked_asset_refs=(),
        )
        return replace(view, shot_bindings=tuple(list(view.shot_bindings) + [shot_binding]))

    def add_candidate_asset(
        self,
        view: ActionReplicaPlanningView,
        *,
        asset_type: str,
        label: str,
        source: str,
        scope_type: str,
        scope_id: str,
        asset_ref: str | None = None,
        confidence: float = 0.5,
        evidence: list[str] | tuple[str, ...] | None = None,
    ) -> ActionReplicaPlanningView:
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
            view,
            candidate_assets=tuple(list(view.candidate_assets) + [candidate]),
        )
        updated = self._attach_asset_ref(
            updated,
            scope_type=candidate.scope_type,
            scope_id=candidate.scope_id,
            candidate_ref=candidate.candidate_id,
            linked_ref=None,
        )
        return self.rebuild_usage_index(updated)

    def link_candidate_asset(
        self,
        view: ActionReplicaPlanningView,
        *,
        candidate_id: str,
        asset_ref: str,
        accepted_by: str,
        usage_scope: str = "shot",
    ) -> ActionReplicaPlanningView:
        candidate = next((item for item in view.candidate_assets if item.candidate_id == candidate_id), None)
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
            view,
            linked_assets=tuple(list(view.linked_assets) + [linked]),
        )
        updated = self._attach_asset_ref(
            updated,
            scope_type=linked.scope_type,
            scope_id=linked.scope_id,
            candidate_ref=None,
            linked_ref=linked.link_id,
        )
        return self.rebuild_usage_index(updated)

    def rebuild_usage_index(self, view: ActionReplicaPlanningView) -> ActionReplicaPlanningView:
        usage_records: list[PlanningUsageRecord] = []
        for candidate in view.candidate_assets:
            if not candidate.asset_ref:
                continue
            usage_records.append(
                PlanningUsageRecord(
                    usage_id=f"usage-{uuid4().hex[:10]}",
                    line_id=view.line_id,
                    planning_id=view.planning_id,
                    run_ref=view.run_ref,
                    step_id="planning",
                    scope_type=candidate.scope_type,
                    scope_id=candidate.scope_id,
                    asset_ref=candidate.asset_ref,
                    usage_role=self._usage_role_for_scope(candidate.scope_type),
                    source_state="candidate",
                    source_id=candidate.candidate_id,
                )
            )
        for linked in view.linked_assets:
            usage_records.append(
                PlanningUsageRecord(
                    usage_id=f"usage-{uuid4().hex[:10]}",
                    line_id=view.line_id,
                    planning_id=view.planning_id,
                    run_ref=view.run_ref,
                    step_id="planning",
                    scope_type=linked.scope_type,
                    scope_id=linked.scope_id,
                    asset_ref=linked.asset_ref,
                    usage_role=self._usage_role_for_scope(linked.scope_type),
                    source_state="linked",
                    source_id=linked.link_id,
                )
            )
        return replace(view, file_usage_index=tuple(usage_records))

    def build_execution_needs(self, view: ActionReplicaPlanningView) -> tuple[ActionReplicaExecutionNeed, ...]:
        needs: list[ActionReplicaExecutionNeed] = []
        for role_binding in view.role_bindings:
            identity_refs, identity_state = self._resolve_scope_asset_refs(view, "replica", role_binding.replica_id)
            if identity_refs:
                needs.append(
                    ActionReplicaExecutionNeed(
                        need_id=f"need-{uuid4().hex[:10]}",
                        line_id=view.line_id,
                        planning_id=view.planning_id,
                        need_kind="identity_reference",
                        scope_type="role",
                        scope_id=role_binding.role_binding_id,
                        role_binding_id=role_binding.role_binding_id,
                        shot_binding_id=None,
                        asset_refs=identity_refs,
                        source_state=identity_state,
                    )
                )
            if role_binding.wardrobe_id:
                wardrobe_refs, wardrobe_state = self._resolve_scope_asset_refs(view, "wardrobe", role_binding.wardrobe_id)
                if wardrobe_refs:
                    needs.append(
                        ActionReplicaExecutionNeed(
                            need_id=f"need-{uuid4().hex[:10]}",
                            line_id=view.line_id,
                            planning_id=view.planning_id,
                            need_kind="wardrobe_reference",
                            scope_type="role",
                            scope_id=role_binding.role_binding_id,
                            role_binding_id=role_binding.role_binding_id,
                            shot_binding_id=None,
                            asset_refs=wardrobe_refs,
                            source_state=wardrobe_state,
                        )
                    )
            for prop_id in role_binding.default_prop_ids:
                prop_refs, prop_state = self._resolve_scope_asset_refs(view, "prop", prop_id)
                if prop_refs:
                    needs.append(
                        ActionReplicaExecutionNeed(
                            need_id=f"need-{uuid4().hex[:10]}",
                            line_id=view.line_id,
                            planning_id=view.planning_id,
                            need_kind="prop_reference",
                            scope_type="role",
                            scope_id=role_binding.role_binding_id,
                            role_binding_id=role_binding.role_binding_id,
                            shot_binding_id=None,
                            asset_refs=prop_refs,
                            source_state=prop_state,
                        )
                    )
        for shot_binding in view.shot_bindings:
            shot_refs, shot_state = self._resolve_scope_asset_refs(view, "shot", shot_binding.shot_id)
            if shot_refs:
                needs.append(
                    ActionReplicaExecutionNeed(
                        need_id=f"need-{uuid4().hex[:10]}",
                        line_id=view.line_id,
                        planning_id=view.planning_id,
                        need_kind="shot_reference",
                        scope_type="shot",
                        scope_id=shot_binding.shot_id,
                        role_binding_id=(shot_binding.role_binding_ids[0] if shot_binding.role_binding_ids else None),
                        shot_binding_id=shot_binding.shot_binding_id,
                        asset_refs=shot_refs,
                        source_state=shot_state,
                    )
                )
        return tuple(needs)

    @staticmethod
    def _usage_role_for_scope(scope_type: str) -> str:
        mapping = {
            "replica": "identity_reference",
            "wardrobe": "wardrobe_reference",
            "prop": "prop_reference",
            "shot": "shot_reference",
        }
        return mapping.get(str(scope_type or "").strip(), "prompt_input")

    @staticmethod
    def _resolve_scope_asset_refs(
        view: ActionReplicaPlanningView,
        scope_type: str,
        scope_id: str,
    ) -> tuple[tuple[str, ...], str]:
        linked_refs = tuple(
            linked.asset_ref
            for linked in view.linked_assets
            if linked.scope_type == scope_type and linked.scope_id == scope_id and str(linked.asset_ref or "").strip()
        )
        if linked_refs:
            return linked_refs, "linked"
        candidate_refs = tuple(
            candidate.asset_ref
            for candidate in view.candidate_assets
            if candidate.scope_type == scope_type and candidate.scope_id == scope_id and str(candidate.asset_ref or "").strip()
        )
        if candidate_refs:
            return candidate_refs, "candidate"
        return (), "missing"

    @staticmethod
    def _attach_asset_ref(
        view: ActionReplicaPlanningView,
        *,
        scope_type: str,
        scope_id: str,
        candidate_ref: str | None,
        linked_ref: str | None,
    ) -> ActionReplicaPlanningView:
        normalized_scope = str(scope_type or "").strip()
        normalized_id = str(scope_id or "").strip()
        if normalized_scope == "replica":
            identities = []
            for identity in view.identities:
                if identity.replica_id != normalized_id:
                    identities.append(identity)
                    continue
                candidate_refs = list(identity.identity_asset_candidate_refs)
                linked_refs = list(identity.identity_asset_link_refs)
                if candidate_ref and candidate_ref not in candidate_refs:
                    candidate_refs.append(candidate_ref)
                if linked_ref and linked_ref not in linked_refs:
                    linked_refs.append(linked_ref)
                identities.append(
                    replace(
                        identity,
                        identity_asset_candidate_refs=tuple(candidate_refs),
                        identity_asset_link_refs=tuple(linked_refs),
                    )
                )
            return replace(view, identities=tuple(identities))
        if normalized_scope == "wardrobe":
            wardrobes = []
            for wardrobe in view.wardrobes:
                if wardrobe.wardrobe_id != normalized_id:
                    wardrobes.append(wardrobe)
                    continue
                candidate_refs = list(wardrobe.asset_candidate_refs)
                linked_refs = list(wardrobe.asset_link_refs)
                if candidate_ref and candidate_ref not in candidate_refs:
                    candidate_refs.append(candidate_ref)
                if linked_ref and linked_ref not in linked_refs:
                    linked_refs.append(linked_ref)
                wardrobes.append(
                    replace(
                        wardrobe,
                        asset_candidate_refs=tuple(candidate_refs),
                        asset_link_refs=tuple(linked_refs),
                    )
                )
            return replace(view, wardrobes=tuple(wardrobes))
        if normalized_scope == "prop":
            hand_props = []
            for hand_prop in view.hand_props:
                if hand_prop.prop_id != normalized_id:
                    hand_props.append(hand_prop)
                    continue
                candidate_refs = list(hand_prop.asset_candidate_refs)
                linked_refs = list(hand_prop.asset_link_refs)
                if candidate_ref and candidate_ref not in candidate_refs:
                    candidate_refs.append(candidate_ref)
                if linked_ref and linked_ref not in linked_refs:
                    linked_refs.append(linked_ref)
                hand_props.append(
                    replace(
                        hand_prop,
                        asset_candidate_refs=tuple(candidate_refs),
                        asset_link_refs=tuple(linked_refs),
                    )
                )
            return replace(view, hand_props=tuple(hand_props))
        if normalized_scope == "shot":
            shot_bindings = []
            for shot_binding in view.shot_bindings:
                if shot_binding.shot_id != normalized_id:
                    shot_bindings.append(shot_binding)
                    continue
                candidate_refs = list(shot_binding.candidate_asset_refs)
                linked_refs = list(shot_binding.linked_asset_refs)
                if candidate_ref and candidate_ref not in candidate_refs:
                    candidate_refs.append(candidate_ref)
                if linked_ref and linked_ref not in linked_refs:
                    linked_refs.append(linked_ref)
                shot_bindings.append(
                    replace(
                        shot_binding,
                        candidate_asset_refs=tuple(candidate_refs),
                        linked_asset_refs=tuple(linked_refs),
                    )
                )
            return replace(view, shot_bindings=tuple(shot_bindings))
        return view

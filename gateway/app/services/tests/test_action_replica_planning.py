from gateway.app.services.planning.action_replica_planning import (
    ACTION_REPLICA_LINE_ID,
    ActionReplicaPlanningService,
    PlanningBindingStatus,
)
from gateway.app.services.planning.script_video_planning import PlanningDraftStatus


def _build_bound_view():
    service = ActionReplicaPlanningService()
    view = service.create_view(
        planning_id="replica-plan-001",
        source_ref="planning://action-replica/source-001",
        run_ref="run-001",
    )
    view = service.add_replica_identity(
        view,
        display_name="Creator A",
        persona_notes="Beauty tutorial host",
    )
    view = service.add_wardrobe(
        view,
        replica_id=view.identities[0].replica_id,
        look_label="Pink blazer look",
        style_notes="clean premium look",
    )
    view = service.add_hand_prop(
        view,
        display_name="Lip gloss",
        usage_notes="held in opening shot",
    )
    view = service.bind_role(
        view,
        role_name="host",
        replica_id=view.identities[0].replica_id,
        wardrobe_id=view.wardrobes[0].wardrobe_id,
        default_prop_ids=(view.hand_props[0].prop_id,),
    )
    view = service.bind_shot(
        view,
        shot_id="shot-001",
        role_binding_ids=(view.role_bindings[0].role_binding_id,),
        prop_ids=(view.hand_props[0].prop_id,),
        camera_action_hint="close_up",
        motion_hint="pick_up_product",
    )
    return service, view


def test_action_replica_planning_view_builds_assets_and_bindings():
    _, view = _build_bound_view()

    assert view.line_id == ACTION_REPLICA_LINE_ID
    assert view.status == PlanningDraftStatus.DRAFT
    assert len(view.identities) == 1
    assert len(view.wardrobes) == 1
    assert len(view.hand_props) == 1
    assert len(view.role_bindings) == 1
    assert len(view.shot_bindings) == 1
    assert view.role_bindings[0].status == PlanningBindingStatus.DRAFT
    assert view.role_bindings[0].replica_id == view.identities[0].replica_id
    assert view.role_bindings[0].wardrobe_id == view.wardrobes[0].wardrobe_id
    assert view.role_bindings[0].default_prop_ids == (view.hand_props[0].prop_id,)
    assert view.shot_bindings[0].role_binding_ids == (view.role_bindings[0].role_binding_id,)
    assert view.shot_bindings[0].prop_ids == (view.hand_props[0].prop_id,)


def test_action_replica_candidate_and_linked_assets_remain_dual_state_with_usage_index():
    service, view = _build_bound_view()

    view = service.add_candidate_asset(
        view,
        asset_type="identity_reference",
        label="Creator portrait",
        source="planner",
        scope_type="replica",
        scope_id=view.identities[0].replica_id,
        asset_ref="asset://candidate-replica",
        evidence=["front-facing still"],
    )
    view = service.add_candidate_asset(
        view,
        asset_type="wardrobe_reference",
        label="Blazer reference",
        source="planner",
        scope_type="wardrobe",
        scope_id=view.wardrobes[0].wardrobe_id,
        asset_ref="asset://candidate-wardrobe",
    )
    view = service.add_candidate_asset(
        view,
        asset_type="prop_reference",
        label="Lip gloss product",
        source="planner",
        scope_type="prop",
        scope_id=view.hand_props[0].prop_id,
        asset_ref="asset://candidate-prop",
    )
    view = service.add_candidate_asset(
        view,
        asset_type="shot_reference",
        label="Mirror vanity shot",
        source="planner",
        scope_type="shot",
        scope_id=view.shot_bindings[0].shot_id,
        asset_ref="asset://candidate-shot",
    )
    view = service.link_candidate_asset(
        view,
        candidate_id=view.candidate_assets[0].candidate_id,
        asset_ref="asset://linked-replica",
        accepted_by="operator",
        usage_scope="role",
    )
    view = service.link_candidate_asset(
        view,
        candidate_id=view.candidate_assets[3].candidate_id,
        asset_ref="asset://linked-shot",
        accepted_by="operator",
        usage_scope="shot",
    )

    usage_roles = {usage.usage_role for usage in view.file_usage_index}
    source_states = {usage.source_state for usage in view.file_usage_index}

    assert len(view.candidate_assets) == 4
    assert len(view.linked_assets) == 2
    assert view.identities[0].identity_asset_candidate_refs == (view.candidate_assets[0].candidate_id,)
    assert view.identities[0].identity_asset_link_refs == (view.linked_assets[0].link_id,)
    assert view.shot_bindings[0].candidate_asset_refs == (view.candidate_assets[3].candidate_id,)
    assert view.shot_bindings[0].linked_asset_refs == (view.linked_assets[1].link_id,)
    assert usage_roles >= {
        "identity_reference",
        "wardrobe_reference",
        "prop_reference",
        "shot_reference",
    }
    assert source_states >= {"candidate", "linked"}
    assert all(usage.line_id == ACTION_REPLICA_LINE_ID for usage in view.file_usage_index)
    assert all(usage.run_ref == "run-001" for usage in view.file_usage_index)
    assert all(usage.step_id == "planning" for usage in view.file_usage_index)


def test_action_replica_execution_need_mapping_prefers_linked_refs_over_candidates():
    service, view = _build_bound_view()

    view = service.add_candidate_asset(
        view,
        asset_type="identity_reference",
        label="Creator portrait",
        source="planner",
        scope_type="replica",
        scope_id=view.identities[0].replica_id,
        asset_ref="asset://candidate-replica",
    )
    view = service.add_candidate_asset(
        view,
        asset_type="wardrobe_reference",
        label="Blazer reference",
        source="planner",
        scope_type="wardrobe",
        scope_id=view.wardrobes[0].wardrobe_id,
        asset_ref="asset://candidate-wardrobe",
    )
    view = service.add_candidate_asset(
        view,
        asset_type="prop_reference",
        label="Lip gloss product",
        source="planner",
        scope_type="prop",
        scope_id=view.hand_props[0].prop_id,
        asset_ref="asset://candidate-prop",
    )
    view = service.add_candidate_asset(
        view,
        asset_type="shot_reference",
        label="Mirror vanity shot",
        source="planner",
        scope_type="shot",
        scope_id=view.shot_bindings[0].shot_id,
        asset_ref="asset://candidate-shot",
    )
    view = service.link_candidate_asset(
        view,
        candidate_id=view.candidate_assets[0].candidate_id,
        asset_ref="asset://linked-replica",
        accepted_by="operator",
    )
    view = service.link_candidate_asset(
        view,
        candidate_id=view.candidate_assets[1].candidate_id,
        asset_ref="asset://linked-wardrobe",
        accepted_by="operator",
    )
    view = service.link_candidate_asset(
        view,
        candidate_id=view.candidate_assets[2].candidate_id,
        asset_ref="asset://linked-prop",
        accepted_by="operator",
    )

    needs = service.build_execution_needs(view)
    needs_by_kind = {need.need_kind: need for need in needs}

    assert set(needs_by_kind) >= {
        "identity_reference",
        "wardrobe_reference",
        "prop_reference",
        "shot_reference",
    }
    assert needs_by_kind["identity_reference"].asset_refs == ("asset://linked-replica",)
    assert needs_by_kind["identity_reference"].source_state == "linked"
    assert needs_by_kind["wardrobe_reference"].asset_refs == ("asset://linked-wardrobe",)
    assert needs_by_kind["prop_reference"].asset_refs == ("asset://linked-prop",)
    assert needs_by_kind["shot_reference"].asset_refs == ("asset://candidate-shot",)
    assert needs_by_kind["shot_reference"].source_state == "candidate"
    assert needs_by_kind["identity_reference"].role_binding_id == view.role_bindings[0].role_binding_id
    assert needs_by_kind["shot_reference"].shot_binding_id == view.shot_bindings[0].shot_binding_id

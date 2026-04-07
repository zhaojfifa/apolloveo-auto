from gateway.app.services.planning.prompt_registry import (
    SCRIPT_VIDEO_PROMPT_REGISTRY_REF,
    load_planning_prompt_registry,
)
from gateway.app.services.planning.script_video_planning import (
    PlanningDraftStatus,
    ScriptVideoPlanningService,
)


def test_script_video_planning_registry_resolves_default_template():
    registry = load_planning_prompt_registry()

    template = registry.resolve_default(category="shot_planning", family="story_beats")

    assert registry.line_id == "script_video_line"
    assert registry.registry_ref == SCRIPT_VIDEO_PROMPT_REGISTRY_REF
    assert template is not None
    assert template.template_id == "script_video.story_beats.default"
    assert template.is_default is True


def test_script_video_planning_service_builds_draft_with_segments_shots_and_entities():
    service = ScriptVideoPlanningService()

    draft = service.create_draft(
        planning_id="plan-001",
        source_ref="script://source-001",
        run_ref="run-001",
        script_input="Host introduces the product.\n\nHost shows the final result.",
        entity_hints={
            "roles": ["Host"],
            "scenes": ["Bathroom"],
            "props": ["Lipstick"],
        },
    )

    assert draft.line_id == "script_video_line"
    assert draft.status == PlanningDraftStatus.DRAFT
    assert draft.prompt_template_registry_ref == SCRIPT_VIDEO_PROMPT_REGISTRY_REF
    assert draft.prompt_template_ref == "script_video.story_beats.default"
    assert len(draft.segments) == 2
    assert len(draft.shots) == 2
    assert draft.shots[0].segment_id == draft.segments[0].segment_id
    assert [entity.entity_type for entity in draft.extracted_entities] == ["role", "scene", "prop"]
    assert all(usage.line_id == "script_video_line" for usage in draft.file_usage_index)
    assert any(usage.usage_role == "prompt_input" for usage in draft.file_usage_index)


def test_script_video_candidate_and_linked_assets_remain_dual_state():
    service = ScriptVideoPlanningService()
    draft = service.create_draft(
        planning_id="plan-002",
        source_ref="script://source-002",
        script_input="Host opens the product box.",
    )

    draft_with_candidate = service.add_candidate_asset(
        draft,
        asset_type="reference_image",
        label="Host portrait",
        source="planner",
        scope_type="shot",
        scope_id=draft.shots[0].shot_id,
        asset_ref="asset://candidate-host-portrait",
        evidence=["intro frame"],
    )
    candidate = draft_with_candidate.candidate_assets[0]

    linked_draft = service.link_candidate_asset(
        draft_with_candidate,
        candidate_id=candidate.candidate_id,
        asset_ref="asset://linked-host-portrait",
        accepted_by="operator",
        usage_scope="shot",
    )

    assert len(linked_draft.candidate_assets) == 1
    assert len(linked_draft.linked_assets) == 1
    assert linked_draft.candidate_assets[0].candidate_id == candidate.candidate_id
    assert linked_draft.linked_assets[0].linked_from_candidate_id == candidate.candidate_id
    assert candidate.candidate_id in linked_draft.shots[0].candidate_asset_refs
    assert linked_draft.linked_assets[0].link_id in linked_draft.shots[0].linked_asset_refs


def test_script_video_usage_index_tracks_candidate_and_linked_records_by_line_and_run():
    service = ScriptVideoPlanningService()
    draft = service.create_draft(
        planning_id="plan-003",
        source_ref="script://source-003",
        run_ref="run-003",
        script_input="Creator demonstrates the routine.",
    )
    draft = service.add_candidate_asset(
        draft,
        asset_type="scene_reference",
        label="Vanity table",
        source="planner",
        scope_type="shot",
        scope_id=draft.shots[0].shot_id,
        asset_ref="asset://candidate-scene",
    )
    draft = service.link_candidate_asset(
        draft,
        candidate_id=draft.candidate_assets[0].candidate_id,
        asset_ref="asset://linked-scene",
        accepted_by="operator",
    )

    usage_roles = {usage.usage_role for usage in draft.file_usage_index}
    source_states = {usage.source_state for usage in draft.file_usage_index}

    assert usage_roles >= {"prompt_input", "candidate", "linked"}
    assert source_states >= {"registry", "candidate", "linked"}
    assert all(usage.line_id == "script_video_line" for usage in draft.file_usage_index)
    assert all(usage.run_ref == "run-003" for usage in draft.file_usage_index)
    assert all(usage.step_id == "planning" for usage in draft.file_usage_index)

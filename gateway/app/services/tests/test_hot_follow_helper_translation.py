from gateway.app.services.hot_follow_helper_translation import helper_translate_lane_state


def test_helper_translate_lane_state_distinguishes_pending_temporary_terminal_and_not_involved():
    pending = helper_translate_lane_state(
        {},
        translation_waiting=True,
        helper_source_text="voice led transcript",
    )
    temporary = helper_translate_lane_state(
        {
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "retry later",
            "subtitle_helper_provider": "gemini",
        },
        translation_waiting=True,
        helper_source_text="voice led transcript",
    )
    terminal = helper_translate_lane_state(
        {
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_terminal_failure",
            "subtitle_helper_provider": "gemini",
        },
        translation_waiting=True,
        helper_source_text="voice led transcript",
    )
    not_involved = helper_translate_lane_state(
        {},
        translation_waiting=False,
        helper_source_text="",
    )

    assert pending["status"] == "helper_output_pending"
    assert pending["output_state"] == "helper_output_pending"
    assert pending["provider_health"] == "provider_ok"
    assert pending["visibility"] == "pending_provider_work"
    assert pending["retryable"] is True
    assert pending["terminal"] is False

    assert temporary["status"] == "helper_output_unavailable"
    assert temporary["output_state"] == "helper_output_unavailable"
    assert temporary["provider_health"] == "provider_retryable_failure"
    assert temporary["visibility"] == "temporary_provider_issue"
    assert temporary["failed"] is True
    assert temporary["retryable"] is True

    assert terminal["status"] == "helper_output_unavailable"
    assert terminal["output_state"] == "helper_output_unavailable"
    assert terminal["provider_health"] == "provider_terminal_failure"
    assert terminal["visibility"] == "terminal_provider_failure"
    assert terminal["terminal"] is True
    assert terminal["retryable"] is False

    assert not_involved["status"] == "helper_output_unavailable"
    assert not_involved["output_state"] == "helper_output_unavailable"
    assert not_involved["provider_health"] == "provider_ok"
    assert not_involved["visibility"] == "no_helper_used"
    assert not_involved["failed"] is False


def test_helper_translate_lane_state_supports_resolved_output_with_retryable_provider_warning():
    resolved_warning = helper_translate_lane_state(
        {
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "retry later",
            "subtitle_helper_provider": "gemini",
            "subtitle_helper_input_text": "this is you",
            "subtitle_helper_translated_text": "đây là bạn",
            "subtitle_helper_target_lang": "vi",
        },
        translation_waiting=False,
        helper_source_text="this is you",
        helper_output_consumed=True,
    )

    assert resolved_warning["status"] == "helper_resolved_with_retryable_provider_warning"
    assert resolved_warning["output_state"] == "helper_output_resolved"
    assert resolved_warning["provider_health"] == "provider_retryable_failure"
    assert resolved_warning["composite_state"] == "helper_resolved_with_retryable_provider_warning"
    assert resolved_warning["warning_only"] is True
    assert resolved_warning["failed"] is False
    assert resolved_warning["translated_text"] == "đây là bạn"

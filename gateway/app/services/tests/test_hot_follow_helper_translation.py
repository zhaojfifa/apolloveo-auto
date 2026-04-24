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

    assert pending["status"] == "helper_pending"
    assert pending["visibility"] == "pending_provider_work"
    assert pending["retryable"] is True
    assert pending["terminal"] is False

    assert temporary["status"] == "helper_retryable_failure"
    assert temporary["visibility"] == "temporary_provider_issue"
    assert temporary["failed"] is True
    assert temporary["retryable"] is True

    assert terminal["status"] == "helper_terminal_failure"
    assert terminal["visibility"] == "terminal_provider_failure"
    assert terminal["terminal"] is True
    assert terminal["retryable"] is False

    assert not_involved["status"] == "helper_unavailable"
    assert not_involved["visibility"] == "no_helper_used"
    assert not_involved["failed"] is False

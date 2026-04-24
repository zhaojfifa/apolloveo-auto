from gateway.app.services.hot_follow_subtitle_currentness import (
    compute_hot_follow_target_subtitle_currentness,
    has_semantic_target_subtitle_text,
)


SOURCE_SRT = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
MY_TARGET_SRT = "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n"
VI_TARGET_SRT = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"


def _currentness(target_lang: str, target_text: str, **overrides):
    payload = {
        "target_lang": target_lang,
        "target_text": target_text,
        "source_texts": (SOURCE_SRT,),
        "subtitle_artifact_exists": True,
        "expected_subtitle_source": "vi.srt" if target_lang == "vi" else "mm.srt",
        "actual_subtitle_source": "vi.srt" if target_lang == "vi" else "mm.srt",
        "translation_incomplete": False,
        "has_saved_revision": False,
    }
    payload.update(overrides)
    return compute_hot_follow_target_subtitle_currentness(**payload)


def test_myanmar_source_copy_target_subtitle_is_not_current():
    state = _currentness("my", SOURCE_SRT)

    assert state["target_subtitle_current"] is False
    assert state["target_subtitle_current_reason"] == "target_subtitle_source_copy"
    assert state["target_subtitle_source_copy"] is True


def test_myanmar_translation_incomplete_target_subtitle_is_not_current():
    state = _currentness("my", MY_TARGET_SRT, translation_incomplete=True)

    assert state["target_subtitle_current"] is False
    assert state["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"


def test_myanmar_valid_authoritative_target_subtitle_is_current():
    state = _currentness("my", MY_TARGET_SRT)

    assert state["target_subtitle_current"] is True
    assert state["target_subtitle_current_reason"] == "ready"
    assert state["target_subtitle_authoritative_source"] is True


def test_myanmar_legacy_my_srt_alias_is_treated_as_authoritative():
    state = _currentness("my", MY_TARGET_SRT, actual_subtitle_source="my.srt")

    assert state["target_subtitle_current"] is True
    assert state["target_subtitle_current_reason"] == "ready"
    assert state["target_subtitle_authoritative_source"] is True


def test_timing_only_srt_has_no_semantic_target_subtitle_text():
    timing_only = "1\n00:00:00,000 --> 00:00:02,000\n\n"

    assert has_semantic_target_subtitle_text(timing_only) is False

    state = _currentness("my", timing_only)

    assert state["target_subtitle_current"] is False
    assert state["target_subtitle_current_reason"] == "target_subtitle_empty"


def test_vietnamese_currentness_stays_strict_and_valid_target_still_passes():
    source_copy = _currentness("vi", SOURCE_SRT)
    valid = _currentness("vi", VI_TARGET_SRT)

    assert source_copy["target_subtitle_current"] is False
    assert source_copy["target_subtitle_current_reason"] == "target_subtitle_source_copy"
    assert valid["target_subtitle_current"] is True
    assert valid["target_subtitle_current_reason"] == "ready"

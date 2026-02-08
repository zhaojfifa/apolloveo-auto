from gateway.app.services.status_policy.utils import coerce_final_status

def test_deliverable_ready_overrides_error_reason():
    task = {"status":"running", "error_reason":"dub_failed"}
    updates = {"publish_status":"ready", "publish_key":"k.zip"}
    out = coerce_final_status(None, task, updates)
    assert out["status"] == "ready"

def test_deliverable_ready_overrides_failed_substatus():
    task = {"status":"running"}
    updates = {"dub_status":"failed", "publish_status":"ready", "publish_key":"k.zip"}
    out = coerce_final_status(None, task, updates)
    assert out["status"] == "ready"
    assert "dub_failed" in (out.get("warnings") or [])


def test_ready_is_monotonic_with_deliverable():
    task = {"status": "ready", "publish_status": "ready", "publish_key": "k.zip"}
    updates = {"subtitles_status": "failed"}
    out = coerce_final_status(None, task, updates)
    assert out["status"] == "ready"


def test_failed_when_no_deliverable_and_parse_failed():
    task = {"status": "running"}
    updates = {"status": "failed", "error_reason": "parse_failed"}
    out = coerce_final_status(None, task, updates)
    assert out["status"] == "failed"

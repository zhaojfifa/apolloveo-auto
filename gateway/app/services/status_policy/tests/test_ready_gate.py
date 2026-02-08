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

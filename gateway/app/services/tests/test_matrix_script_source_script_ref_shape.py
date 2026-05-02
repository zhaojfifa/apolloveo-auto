"""Server-side ref-shape guard for Matrix Script ``source_script_ref``.

Authority: ``docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md``
§8.A and the source-script-ref shape addendum in
``docs/contracts/matrix_script/task_entry_contract_v1.md``.

The guard exists to stop operators from pasting prose / script body into the
``source_script_ref`` field. The contract requires an opaque reference; the
payload-builder must never see body text. These tests prove the guard at the
service boundary and confirm the create-entry path still produces the formal
Matrix Script payload when a contract-shaped ref is supplied.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router
from gateway.app.services.matrix_script.create_entry import (
    SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES,
    SOURCE_SCRIPT_REF_MAX_LENGTH,
    build_matrix_script_entry,
    build_matrix_script_task_payload,
)


TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def _entry_kwargs(**overrides):
    base = {
        "topic": "新品矩阵脚本",
        "source_script_ref": "content://matrix-script/source/001",
        "source_language": "zh",
        "target_language": "mm",
        "target_platform": "TikTok",
        "variation_target_count": "4",
    }
    base.update(overrides)
    return base


# ----------------------------- rejection branches --------------------------- #


def test_multi_line_prose_body_is_rejected():
    body = (
        "镜头一：开场画面，主角介绍产品功能。\n"
        "镜头二：展示使用场景与卖点对比。\n"
        "镜头三：行动号召，引导关注主页。"
    )
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(**_entry_kwargs(source_script_ref=body))
    assert exc.value.status_code == 400
    assert "single-line" in exc.value.detail


def test_prose_body_with_whitespace_is_rejected_even_when_single_line():
    body = "Open with hook then deliver product value proposition in 30 seconds"
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(**_entry_kwargs(source_script_ref=body))
    assert exc.value.status_code == 400
    assert "whitespace" in exc.value.detail


def test_overlong_ref_is_rejected():
    overlong = "content://" + ("x" * (SOURCE_SCRIPT_REF_MAX_LENGTH + 1))
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(**_entry_kwargs(source_script_ref=overlong))
    assert exc.value.status_code == 400
    assert str(SOURCE_SCRIPT_REF_MAX_LENGTH) in exc.value.detail


def test_unrecognised_scheme_is_rejected():
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(
            **_entry_kwargs(source_script_ref="ftp://legacy/script.txt")
        )
    assert exc.value.status_code == 400
    assert "scheme is not recognised" in exc.value.detail


def test_empty_string_is_still_rejected_as_required():
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(**_entry_kwargs(source_script_ref=""))
    assert exc.value.status_code == 400
    assert exc.value.detail == "source_script_ref is required"


def test_short_token_below_minimum_length_is_rejected():
    with pytest.raises(HTTPException) as exc:
        build_matrix_script_entry(**_entry_kwargs(source_script_ref="ab"))
    assert exc.value.status_code == 400
    assert "recognised opaque reference" in exc.value.detail


# ----------------------------- accepted branches --------------------------- #


@pytest.mark.parametrize(
    "ref",
    [
        "content://matrix-script/source/001",
        "task://matrix-script/2026-05-02/sample-1",
        "asset://library/script/abc-123",
        "ref://operator-cache/seed-99",
        "https://docs.internal.example.com/matrix-script/source-001",
        "http://legacy.internal/scripts/12",
        "s3://bucket/matrix-script/source/001.json",
        "gs://bucket/matrix-script/source/001.json",
        "MS-SRC-2026-04-001",
        "matrix-script.source.001",
        "ABC123-XYZ.456",
    ],
)
def test_contract_shaped_refs_are_accepted(ref):
    entry = build_matrix_script_entry(**_entry_kwargs(source_script_ref=ref))
    assert entry.source_script_ref == ref


def test_accepted_scheme_set_is_complete():
    """Every documented scheme in the contract addendum must round-trip."""

    for scheme in SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES:
        ref = f"{scheme}://matrix-script/source/{scheme}-001"
        entry = build_matrix_script_entry(**_entry_kwargs(source_script_ref=ref))
        assert entry.source_script_ref == ref


# ----------------------------- payload builder still wires ------------------ #


def test_payload_builder_still_constructs_formal_packet_for_valid_ref():
    entry = build_matrix_script_entry(**_entry_kwargs())
    payload = build_matrix_script_task_payload(entry)

    assert payload["kind"] == "matrix_script"
    assert payload["category_key"] == "matrix_script"
    assert payload["platform"] == "matrix_script"
    assert payload["source_url"] == "content://matrix-script/source/001"
    assert payload["config"]["entry"]["source_script_ref"] == (
        "content://matrix-script/source/001"
    )
    assert payload["config"]["line_id"] == "matrix_script"
    assert payload["packet"]["line_id"] == "matrix_script"
    assert {ref["ref_id"] for ref in payload["packet"]["line_specific_refs"]} == {
        "matrix_script_variation_matrix",
        "matrix_script_slot_pack",
    }
    assert {ref["ref_id"] for ref in payload["line_specific_refs"]} == {
        "matrix_script_variation_matrix",
        "matrix_script_slot_pack",
    }


# ----------------------------- HTTP boundary -------------------------------- #


def test_post_handler_rejects_prose_body_with_400(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    class _Repo:
        def create(self, payload):
            raise AssertionError(
                "repo.create must not run when source_script_ref fails the guard"
            )

        def get(self, task_id):  # pragma: no cover - never reached
            raise AssertionError("repo.get must not run on rejection")

    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.post(
            "/tasks/matrix-script/new",
            data={
                "topic": "新品矩阵脚本",
                "source_script_ref": "镜头一：开场画面\n镜头二：展示卖点\n镜头三：行动号召",
                "source_language": "zh",
                "target_language": "mm",
                "target_platform": "TikTok",
                "variation_target_count": "4",
            },
            follow_redirects=False,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "source_script_ref" in response.text


def test_post_handler_accepts_contract_shaped_ref_and_redirects(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    created = {}

    class _Repo:
        def create(self, payload):
            created.update(payload)
            return payload

        def get(self, task_id):
            if created.get("task_id") == task_id:
                return dict(created)
            return None

    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.post(
            "/tasks/matrix-script/new",
            data={
                "topic": "新品矩阵脚本",
                "source_script_ref": "content://matrix-script/source/001",
                "source_language": "zh",
                "target_language": "mm",
                "target_platform": "TikTok",
                "variation_target_count": "4",
            },
            follow_redirects=False,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 303
    assert (
        response.headers["location"]
        == f"/tasks/{created['task_id']}?created=matrix_script"
    )
    assert created["source_url"] == "content://matrix-script/source/001"


# ----------------------------- template wiring ------------------------------ #


def test_template_replaces_textarea_with_pattern_constrained_input():
    template = (TEMPLATE_DIR / "matrix_script_new.html").read_text(encoding="utf-8")

    assert (
        '<textarea id="source_script_ref"' not in template
    ), "source_script_ref must not be a free-form textarea"
    assert 'id="source_script_ref"' in template
    assert 'name="source_script_ref"' in template
    assert 'type="text"' in template
    assert 'maxlength="512"' in template
    assert "pattern=" in template
    assert "content://matrix-script/source/001" in template
    assert "粘贴脚本文本" not in template


def test_template_helper_text_forbids_pasting_body():
    template = (TEMPLATE_DIR / "matrix_script_new.html").read_text(encoding="utf-8")
    assert "不要" in template
    assert "脚本正文" in template

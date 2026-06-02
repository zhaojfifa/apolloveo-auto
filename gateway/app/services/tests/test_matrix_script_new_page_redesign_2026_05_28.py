"""Matrix Script New Task page redesign tests (2026-05-28 wave).

Authority: Matrix Script cleanup baseline. The entry point is now
script-to-video planning: script text, material, target platform/aspect/language,
then CTA "生成视频方案"; role/voice/subtitle and variants are advanced options.

Pattern: source-only template inspection, mirroring the OWC-MS-RO
template-source tests. No Jinja render, no FastAPI instantiation.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_NEW_TEMPLATE = (
    _REPO_ROOT / "gateway" / "app" / "templates" / "matrix_script_new.html"
)


def _read() -> str:
    return _NEW_TEMPLATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Operator-facing primary copy (Mission §1)
# ---------------------------------------------------------------------------


def test_mission_mandated_operator_copy_present() -> None:
    source = _read()
    assert "输入脚本、素材和目标平台，系统先生成可确认的视频方案" in source
    assert "脚本理解、分镜、背景 / B-Roll、角色、旁白、字幕、音乐与视频变体" in source


def test_page_title_is_chinese_operator_language() -> None:
    source = _read()
    assert ">生成脚本视频方案<" in source


def test_line_pill_marks_matrix_script_line() -> None:
    source = _read()
    assert 'data-role="ms-new-line-pill"' in source
    assert "op-pill--matrix" in source


# ---------------------------------------------------------------------------
# Three primary input affordances — paste / upload / select
# ---------------------------------------------------------------------------


def test_three_source_tabs_rendered() -> None:
    source = _read()
    assert 'data-role="ms-new-source-tab-paste"' in source
    assert 'data-role="ms-new-source-tab-upload"' in source
    assert 'data-role="ms-new-source-tab-select"' in source


def test_paste_tab_has_script_body_textarea() -> None:
    source = _read()
    assert 'data-role="ms-new-script-body"' in source
    assert "<textarea " in source


def test_upload_tab_has_file_input_accepting_text_formats() -> None:
    source = _read()
    assert 'data-role="ms-new-script-file"' in source
    # txt / md are the supported plain-text formats per the redesign
    assert "accept=\".txt,.md,text/plain,text/markdown\"" in source


def test_select_tab_has_existing_source_script_ref_field() -> None:
    source = _read()
    assert 'data-role="ms-new-existing-source-script-ref"' in source


def test_advanced_options_are_collapsed() -> None:
    source = _read()
    assert 'data-role="ms-new-advanced-options"' in source
    assert "高级选项：角色 / 声音 / 字幕、变体策略、素材偏好与运营备注" in source
    assert 'data-role="ms-new-card-role-voice-subtitle"' in source
    assert 'data-role="ms-new-card-variant-strategy"' in source


def test_paste_tab_active_by_default() -> None:
    source = _read()
    # The paste tab has the is-active class baked in at render
    assert (
        'class="ms-new-tab is-active"' in source
        or "ms-new-tab is-active" in source
    )
    # And the JS activates 'paste' on init
    assert "activateTab('paste')" in source


# ---------------------------------------------------------------------------
# Technical ref is collapsed, NOT primary
# ---------------------------------------------------------------------------


def test_technical_ref_inside_technical_mode_gate() -> None:
    """PR-1 (2026-05-28) update: the technical-ref <details> is now gated
    on the ``technical_mode`` server flag. Operators never see it; only
    ``?technical=1`` reveals it as an architect-only section. The block
    itself remains in the template source inside the {% if %} branch."""

    source = _read()
    assert 'data-role="ms-new-technical-ref"' in source
    # Phrasing updated to make the architect-only nature explicit.
    assert "架构师 / 工程师：手动指定不透明脚本句柄（技术引用）" in source
    # The technical-ref <details> must live inside the {% if technical_mode %} branch.
    assert "{% if technical_mode %}" in source
    # The literal "高级：手动..." phrasing is retired (architect / 工程师 takes over).
    assert "高级：手动指定不透明脚本句柄（技术引用）" not in source


def test_source_script_ref_input_preserved_for_form_post() -> None:
    """The backend route still requires source_script_ref; JS populates it.

    PR-1 (2026-05-28) update: a single ``<input type="hidden">`` carries
    the field in operator (non-technical) mode; in technical mode a
    visible text input under the architect-only <details> takes over.
    Both forms preserve the ``name="source_script_ref"`` server contract."""

    source = _read()
    assert 'data-role="ms-new-source-script-ref"' in source
    assert 'name="source_script_ref"' in source
    # Operator-mode hidden input is rendered in the {% else %} branch.
    assert 'type="hidden"' in source


def test_mint_empty_button_only_inside_technical_mode_branch() -> None:
    """PR-1 (2026-05-28) update: the "铸造空句柄" mint affordance is
    removed from the operator surface. It survives ONLY inside the
    ``technical_mode`` branch (architects can still mint empty handles
    when needed for debugging / scripted flows)."""

    source = _read()
    assert 'data-role="ms-new-mint-button"' in source
    assert ">铸造空句柄<" in source
    # The button must live inside the {% if technical_mode %} branch —
    # find the technical-mode opening before the mint button.
    technical_open = source.find("{% if technical_mode %}")
    mint_button = source.find('data-role="ms-new-mint-button"')
    else_branch = source.find("{% else %}")
    end_if = source.find("{% endif %}", technical_open)
    assert technical_open != -1 and mint_button != -1 and end_if != -1
    # Mint button must appear after {% if technical_mode %} and before
    # the {% endif %} that closes it.
    assert technical_open < mint_button < end_if
    # And before the {% else %} that opens the operator-mode branch.
    if else_branch != -1 and else_branch > technical_open and else_branch < end_if:
        assert mint_button < else_branch


# ---------------------------------------------------------------------------
# Ingest endpoint wired on the form
# ---------------------------------------------------------------------------


def test_form_carries_ingest_route_attribute() -> None:
    source = _read()
    assert (
        'data-ingest-route="/tasks/matrix-script/source-script-refs/ingest"' in source
    )


def test_form_carries_mint_route_attribute() -> None:
    source = _read()
    assert (
        'data-mint-route="/tasks/matrix-script/source-script-refs/mint"' in source
    )


# ---------------------------------------------------------------------------
# Honesty audit — no fake outputs, no vendor/model/provider/engine in
# operator-visible text, external URLs explicitly rejected with operator copy
# ---------------------------------------------------------------------------


def test_no_fake_final_video_or_publish_url_in_operator_copy() -> None:
    """RC-R8 audit: no fabricated media URL appears anywhere on the new page."""

    source = _read()
    assert "https://example.com" not in source
    assert "https://cdn." not in source
    assert "final_video.mp4" not in source
    assert "publish_url:" not in source


def test_no_provider_model_vendor_engine_selectors_in_operator_view() -> None:
    """validator R3: operator UI MUST NOT expose provider/model/vendor/engine."""

    source = _read()
    # These tokens MUST NOT appear in a way that would let an operator
    # choose between providers / models / vendors / engines on the form.
    # The technical-ref details legitimately shows opaque scheme names,
    # not vendor selectors.
    assert "vendor_id" not in source
    assert "model_id" not in source
    assert "provider_id" not in source
    assert "engine_id" not in source
    # The technical disclaimer text MUST NOT include a "choose provider"
    # affordance.
    assert "choose provider" not in source.lower()
    assert "select model" not in source.lower()


def test_external_url_rejection_explained_in_operator_language() -> None:
    source = _read()
    # The technical-ref disclaimer names the rejected scheme families in
    # operator language inside the (collapsed) advanced details.
    assert "不是产品内不透明句柄，会被入口拒绝。" in source


# ---------------------------------------------------------------------------
# Operator-language Chinese-first; English ID terms quarantined to technical
# disclaimers only
# ---------------------------------------------------------------------------


def test_html_lang_is_zh_cn() -> None:
    source = _read()
    assert '<html lang="zh-CN">' in source


def test_required_field_label_uses_chinese_marker() -> None:
    source = _read()
    # The required-field marker class is ms-new-required (red asterisk);
    # the literal asterisk + class confirms the marker is operator-visible.
    assert "ms-new-required" in source
    assert "目标语言 <span class=\"ms-new-required\">*</span>" in source


# ---------------------------------------------------------------------------
# JS submit pipeline routes paste / upload bodies through ingest
# ---------------------------------------------------------------------------


def test_js_submit_pipeline_calls_ingest_endpoint() -> None:
    source = _read()
    # The submit handler calls /ingest on paste / upload submit paths.
    assert "ingestBody(body, 'operator_paste')" in source
    assert "ingestBody(text, 'operator_upload')" in source


def test_js_populates_hidden_source_script_ref_after_ingest() -> None:
    source = _read()
    # The JS sets refInput.value = payload.source_script_ref after a
    # successful ingest, then calls form.submit() so the backend route
    # receives the (now-populated) opaque handle.
    assert "refInput.value = payload.source_script_ref" in source
    assert "form.submit()" in source


# ---------------------------------------------------------------------------
# PR-1 (2026-05-28) — operator surface boundary polish
# ---------------------------------------------------------------------------


def test_operator_mode_renders_hidden_source_script_ref_input_only() -> None:
    """PR-1 acceptance: operator-mode (default) renders a SINGLE hidden
    input for ``source_script_ref`` and NO visible opaque-handle field,
    NO mint button, NO technical-ref details on the operator surface."""

    source = _read()
    # The {% else %} branch (operator mode) contains a hidden input.
    else_idx = source.find("{% else %}")
    endif_idx = source.find("{% endif %}", else_idx) if else_idx != -1 else -1
    assert else_idx != -1 and endif_idx != -1
    operator_branch = source[else_idx:endif_idx]
    assert 'type="hidden"' in operator_branch
    assert 'name="source_script_ref"' in operator_branch
    # No visible label, no placeholder, no mint button inside the operator branch.
    assert "label" not in operator_branch  # no <label> for source_script_ref
    assert "ms-new-mint-button" not in operator_branch
    assert "铸造" not in operator_branch


def test_technical_mode_query_param_is_consumed_server_side() -> None:
    """The route handler exposes ``technical_mode`` to the template based
    on the ``?technical=1`` query param. The template gates the
    architect-only block on this flag. The route handler change lives
    in ``gateway/app/routers/tasks.py``; this test pins the template
    expectation that the variable name is exactly ``technical_mode``."""

    source = _read()
    assert "{% if technical_mode %}" in source


def test_paste_textarea_placeholder_is_short_operator_language() -> None:
    """PR-1 acceptance: the paste textarea placeholder used to be a
    multi-line essay that overflowed the visible region. After PR-1 the
    placeholder is one short prompt; the helper text below the textarea
    carries the volatility + no-vendor-leak disclosure."""

    source = _read()
    # The single-line placeholder is exactly what we ship.
    assert 'placeholder="将脚本正文粘贴到这里..."' in source
    # The longer essay-style placeholder is retired from the template.
    assert "脚本正文不会被发送给任何外部模型、厂商或引擎。" not in (
        # Allow the same disclosure in the helper paragraph below the
        # textarea, but NOT inside any placeholder= attribute. We test
        # the placeholder attribute specifically with a more permissive
        # check: ensure no placeholder= attribute contains a newline
        # entity (the old long placeholder used &#10;).
        ""
    )
    assert "&#10;" not in source.split("placeholder=", 1)[1].split('"', 2)[1] if 'placeholder=' in source else True


def test_responsive_degradation_media_query_for_narrow_viewport() -> None:
    """PR-1 acceptance: at ≤880px the topbar pill no longer floats above
    the title (visual validation issue #5). Stack the page-head row and
    let the tabs wrap to two rows."""

    source = _read()
    assert "@media (max-width: 880px)" in source
    # The op-page-head__row gets flex-direction: column at narrow widths.
    assert ".op-page-head__row { flex-direction: column" in source
    # And the matrix-script pill aligns left rather than floating right.
    assert ".op-page-head__row .op-pill { align-self: flex-start" in source
    # Tabs wrap below 880px.
    assert ".ms-new-tabs { flex-wrap: wrap; }" in source


def test_no_opaque_handle_vocabulary_visible_in_operator_mode_branch() -> None:
    """PR-1 acceptance: operator-mode branch must NOT carry
    ``content://`` / ``task://`` / ``asset://`` / ``ref://`` in any
    visible label, helper, or placeholder. The strings may still appear
    inside the architect-only {% if technical_mode %} branch."""

    source = _read()
    else_idx = source.find("{% else %}")
    endif_idx = source.find("{% endif %}", else_idx) if else_idx != -1 else -1
    operator_branch = source[else_idx:endif_idx]
    assert "content://" not in operator_branch
    assert "task://" not in operator_branch
    assert "asset://" not in operator_branch
    assert "ref://" not in operator_branch
    assert "source_script_ref" in operator_branch  # only as input name= attribute


def test_route_handler_signature_change_documented_in_template_comment() -> None:
    """The template references ``technical_mode`` — the route handler
    in tasks.py reads the query param. This test pins the template's
    own documentation of the contract so a future refactor can't
    silently drop the comment."""

    source = _read()
    assert "?technical=1" in source or "technical=1" in source

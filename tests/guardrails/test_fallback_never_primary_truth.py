"""W2 admission guardrail — fallback / projection / presenter / debug
helpers MUST NOT become primary truth authority.

Authority:
- `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
  §3.4, §7 (no second truth/fallback state semantic)
- `docs/donor/swiftcraft_donor_boundary_v1.md` §4.4 (forbidden decision
  logic — fallback paths must not promote to primary truth) and §5.4
  (truth-write rule)
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.4

Rule:
    Truth-authority runtime modules MUST NOT import projection helpers,
    presenters, `*_fallback*` helpers, or `*_debug` panels. The truth
    direction is one-way: truth-authority modules emit facts; projection /
    presenter / fallback / debug code consumes them.

    Importing a presenter or projection helper into a truth-authority
    module silently inverts that direction and lets a "fallback view"
    re-enter the system as primary truth.

Truth zones (this list IS the authority surface for the test):
    - gateway/app/services/contract_runtime/
    - gateway/app/services/ready_gate/
    - gateway/app/services/packet/
    - gateway/app/domain/
    - gateway/app/services/hot_follow_subtitle_authority.py
"""
from __future__ import annotations

from pathlib import Path

from tests.guardrails._scan import REPO_ROOT, imported_names, iter_py_files


TRUTH_ZONE_DIRS = [
    REPO_ROOT / "gateway" / "app" / "services" / "contract_runtime",
    REPO_ROOT / "gateway" / "app" / "services" / "ready_gate",
    REPO_ROOT / "gateway" / "app" / "services" / "packet",
    REPO_ROOT / "gateway" / "app" / "domain",
]
TRUTH_ZONE_FILES = [
    REPO_ROOT / "gateway" / "app" / "services" / "hot_follow_subtitle_authority.py",
]

# Specific Apollo modules currently classified as projection / presenter /
# fallback / debug helpers. Maintained explicitly to avoid accidentally
# matching truth modules that happen to share a substring (e.g.
# `projection_rules_runtime` IS truth — it defines the projection rules
# themselves, not a projected view).
FORBIDDEN_HELPER_MODULES = {
    "gateway.app.services.task_view_presenters",
    "gateway.app.services.task_router_presenters",
    "gateway.app.services.task_view_projection",
    "gateway.app.services.hot_follow_workbench_presenter",
    "gateway.app.routers.matrix_script_panel_debug",
}

# Suffix-based catch-all for future helpers that follow Apollo's naming
# discipline. Any imported module whose dotted-name ends with one of these
# segments is treated as a projection/fallback/debug helper.
FORBIDDEN_HELPER_SUFFIXES = (
    "_presenter",
    "_presenters",
    "_fallback",
    "_panel_debug",
)


def _truth_files() -> list[Path]:
    files: list[Path] = list(iter_py_files(TRUTH_ZONE_DIRS))
    files.extend(p for p in TRUTH_ZONE_FILES if p.exists())
    # Exclude `tests/` subdirectories inside truth zones — guardrails on
    # truth zones target runtime code, not their colocated test suites.
    files = [p for p in files if "tests" not in p.parts]
    return files


def test_truth_zones_do_not_import_projection_or_presenter_or_fallback():
    offenders: list[tuple[Path, str]] = []
    for path in _truth_files():
        for name in imported_names(path):
            if name in FORBIDDEN_HELPER_MODULES:
                offenders.append((path, name))
                continue
            tail = name.split(".")[-1]
            if any(tail.endswith(suf) for suf in FORBIDDEN_HELPER_SUFFIXES):
                offenders.append((path, name))

    assert not offenders, _format_offenders(
        "Truth-authority module imports a projection / presenter / "
        "fallback / debug helper. Truth flows OUT of these modules; "
        "helpers must never be imported back as a primary truth source.",
        offenders,
    )


def test_truth_zone_inventory_is_not_empty():
    """Sanity: at least one truth-zone file must be scanned. If the layout
    is reorganized and these paths disappear, the guardrail must be
    re-pointed before silently passing.
    """
    assert _truth_files(), (
        "No truth-zone Python files found. The fallback-truth guardrail's "
        "zone list is stale and must be updated."
    )


def _format_offenders(header: str, hits: list[tuple[Path, str]]) -> str:
    lines = [header, ""]
    for path, name in sorted({(p.relative_to(REPO_ROOT), n) for p, n in hits}):
        lines.append(f"  - {path}: imports `{name}`")
    return "\n".join(lines)

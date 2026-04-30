"""W2 admission guardrail — donor (SwiftCraft) leak boundary.

Authority:
- `docs/donor/swiftcraft_donor_boundary_v1.md` §5.1 (Path rule), §5.3
  (Import rule), §7 (Front-end isolation)
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.4

Rule:
    No `swiftcraft.*` import may appear anywhere in Apollo source under
    `gateway/` or `tests/`. Donor code is absorbed by re-homing into Apollo
    paths (per boundary §3 mapping); the donor package name MUST NOT
    survive absorption.

Donor-task / donor-engine module names are also screened so that a
forbidden §4 module (e.g. `app.models.task`, `app.engines.*`) cannot be
re-introduced through a stray import statement.
"""
from __future__ import annotations

import ast
from pathlib import Path

from tests.guardrails._scan import REPO_ROOT, find_forbidden, iter_py_files, imported_names


# Apollo-side roots that must remain donor-package-free.
APOLLO_ROOTS = [
    REPO_ROOT / "gateway",
    REPO_ROOT / "tests",
]

# Donor package names that MUST NOT appear as imports in Apollo source.
FORBIDDEN_DONOR_NAMES = {
    "swiftcraft",
    # Donor "task truth" forbidden surface (boundary §4.1):
    "app.models.task",
    # Donor "engine truth" forbidden surface (boundary §4.2):
    "app.engines",
    "app.engines.base",
    "app.engines.registry",
    "app.engines.mock_engine",
}


def test_no_swiftcraft_import_anywhere_in_apollo_source():
    hits = find_forbidden(APOLLO_ROOTS, {"swiftcraft"})
    # Boundary doc itself and donor mapping doc reference the donor package
    # in markdown. They are not `.py` files and therefore are not scanned.
    assert not hits, _format_hits(
        "`swiftcraft.*` import found in Apollo source. The donor package "
        "name MUST NOT survive absorption (boundary §5.1, §5.3).",
        hits,
    )


def test_no_donor_truth_module_imports_in_apollo_source():
    """Forbid donor task-truth / engine-truth modules at the import layer.

    These modules belong to the donor's §4 forbidden surface. Even if a
    sibling adapter is being absorbed legally, dragging in `app.models.task`
    or `app.engines.*` re-introduces a parallel truth source.
    """
    hits = find_forbidden(APOLLO_ROOTS, FORBIDDEN_DONOR_NAMES - {"swiftcraft"})
    # Allow guardrail tests themselves to *name* these modules in module-
    # level constants (used to drive scanning). Only flag actual `import`
    # / `from ... import ...` statements; the AST scan already does this.
    # Filter out hits that come from the guardrail tests themselves to
    # prevent self-detection.
    guardrail_dir = REPO_ROOT / "tests" / "guardrails"
    hits = [(p, n) for p, n in hits if guardrail_dir not in p.parents and p.parent != guardrail_dir]
    assert not hits, _format_hits(
        "Donor truth module imported in Apollo source (boundary §4.1/§4.2 "
        "forbidden surface).",
        hits,
    )


def test_no_swiftcraft_string_in_python_source_outside_donor_docs():
    """Belt-and-suspenders: scan executable gateway string literals for
    the literal token `swiftcraft` (case-insensitive).

    Attribution headers/docstrings are intentionally not executable donor
    package usage; W1 absorption requires those audit strings in absorbed
    media helpers. Import leakage remains covered separately by the AST
    import scan across both `gateway/` and `tests/`.
    """
    needle = "swiftcraft"
    offenders: list[tuple[Path, int]] = []
    for path in iter_py_files([REPO_ROOT / "gateway"]):
        for node in _non_docstring_string_literals(path):
            if needle not in str(node.value).lower():
                continue
            offenders.append((path, getattr(node, "lineno", 0)))

    assert not offenders, "\n".join(
        [f"Literal 'swiftcraft' executable string found in Apollo gateway source:"]
        + [f"  - {p.relative_to(REPO_ROOT)}:{ln}" for p, ln in offenders]
    )


def _non_docstring_string_literals(path: Path) -> list[ast.Constant]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    docstring_nodes: set[ast.AST] = set()
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            docstring_nodes.add(first.value)

    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node not in docstring_nodes
    ]


def _format_hits(header: str, hits: list[tuple[Path, str]]) -> str:
    lines = [header, ""]
    for path, name in sorted({(p.relative_to(REPO_ROOT), n) for p, n in hits}):
        lines.append(f"  - {path}: imports `{name}`")
    return "\n".join(lines)


# Re-export helpers so this module can be loaded standalone if needed.
__all__ = ["imported_names"]

"""Shared AST-based import scanner used by guardrail tests.

These helpers walk a tree of `.py` files, collect their import targets via
`ast`, and let individual guardrail tests assert that no file under a given
zone imports a forbidden module. Using AST instead of substring search
avoids matching docstrings, comments, or string literals.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]


def iter_py_files(roots: Iterable[Path]) -> Iterator[Path]:
    """Yield every `.py` file under each root, skipping caches and dotdirs."""
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            parts = set(path.parts)
            if "__pycache__" in parts:
                continue
            if any(p.startswith(".") for p in parts):
                continue
            yield path


def imported_names(path: Path) -> set[str]:
    """Return the set of import target names for a single python file.

    For `import a.b.c` -> includes `a.b.c` (and `a`, `a.b` prefixes).
    For `from a.b import c` -> includes `a.b` (and `a` prefix).
    Relative imports (`from . import x`) are skipped — they cannot reach
    third-party SDK or donor packages.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.update(_prefixes(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                names.update(_prefixes(node.module))
    return names


def _prefixes(dotted: str) -> Iterable[str]:
    parts = dotted.split(".")
    for i in range(1, len(parts) + 1):
        yield ".".join(parts[:i])


def find_forbidden(
    roots: Iterable[Path],
    forbidden: Iterable[str],
) -> list[tuple[Path, str]]:
    """Return [(file, forbidden_name)] for each forbidden import found."""
    forbidden_set = set(forbidden)
    hits: list[tuple[Path, str]] = []
    for path in iter_py_files(roots):
        for name in imported_names(path):
            if name in forbidden_set:
                hits.append((path, name))
    return hits

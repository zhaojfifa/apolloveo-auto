from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import yaml

from gateway.app.services.line_binding_service import get_line_runtime_binding


REPO_ROOT = Path(__file__).resolve().parents[4]
_YAML_CODE_BLOCK_RE = re.compile(r"```yaml\s+(.*?)\s+```", re.DOTALL)


@dataclass(frozen=True)
class ContractRuntimeRefs:
    line_id: str | None
    ready_gate_ref: str | None
    projection_rules_ref: str | None
    status_policy_ref: str | None


def resolve_repo_path(ref: str) -> Path:
    path = Path(str(ref or "").strip())
    if not str(path):
        raise RuntimeError("empty contract runtime ref")
    return path if path.is_absolute() else (REPO_ROOT / path)


@lru_cache(maxsize=32)
def load_markdown_yaml_sections(ref: str) -> dict[str, Any]:
    path = resolve_repo_path(ref)
    text = path.read_text(encoding="utf-8")
    sections: dict[str, Any] = {}
    for match in _YAML_CODE_BLOCK_RE.finditer(text):
        payload = yaml.safe_load(match.group(1)) or {}
        if isinstance(payload, dict):
            sections.update(payload)
    if not sections:
        raise RuntimeError(f"no yaml contract blocks found in {ref}")
    return sections


def get_contract_runtime_refs(task_or_kind: dict[str, Any] | str | None) -> ContractRuntimeRefs:
    binding = get_line_runtime_binding(task_or_kind)
    line = binding.line
    if line is None:
        return ContractRuntimeRefs(
            line_id=None,
            ready_gate_ref=None,
            projection_rules_ref=None,
            status_policy_ref=None,
        )
    return ContractRuntimeRefs(
        line_id=line.line_id,
        ready_gate_ref=line.ready_gate_ref or None,
        projection_rules_ref=line.projection_rules_ref or None,
        status_policy_ref=line.status_policy_ref or None,
    )

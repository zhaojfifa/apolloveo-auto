from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import importlib.util
from pathlib import Path
from typing import Any, Callable

import yaml

from gateway.app.lines.base import ProductionLine


SkillRunner = Callable[..., dict[str, Any] | None]


@dataclass(frozen=True)
class LoadedSkillsBundle:
    bundle_id: str
    line_id: str
    bundle_ref: str
    hook_kind: str
    defaults: dict[str, Any]
    stage_order: tuple[str, ...]
    stage_runners: dict[str, SkillRunner]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _bundle_path(bundle_ref: str) -> Path:
    return (_repo_root() / bundle_ref).resolve()


def _load_module_from_path(module_name: str, module_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load skills module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_stage_runner(stage: str, module: Any) -> SkillRunner:
    runner = getattr(module, "run", None)
    if not callable(runner):
        raise RuntimeError(f"skills stage '{stage}' is missing callable run()")
    return runner


@lru_cache(maxsize=16)
def _load_bundle(bundle_ref: str, line_id: str) -> LoadedSkillsBundle:
    bundle_path = _bundle_path(bundle_ref)
    defaults_path = bundle_path / "config" / "defaults.yaml"
    defaults = yaml.safe_load(defaults_path.read_text(encoding="utf-8")) or {}
    stage_order = tuple(defaults.get("stage_order") or ("input", "routing", "quality", "recovery"))
    stage_runners: dict[str, SkillRunner] = {}
    for stage in stage_order:
        stage_id = str(stage or "").strip()
        if not stage_id:
            continue
        module_name = f"apolloveo_skills_{line_id}_{stage_id}"
        module_path = bundle_path / f"{stage_id}_skill.py"
        module = _load_module_from_path(module_name, module_path)
        stage_runners[stage_id] = _validate_stage_runner(stage_id, module)
    bundle_id = str(defaults.get("bundle_id") or f"{line_id}_skills")
    hook_kind = str(defaults.get("hook_kind") or "runtime")
    return LoadedSkillsBundle(
        bundle_id=bundle_id,
        line_id=line_id,
        bundle_ref=bundle_ref,
        hook_kind=hook_kind,
        defaults=defaults,
        stage_order=stage_order,
        stage_runners=stage_runners,
    )


def load_line_skills_bundle(line: ProductionLine | None) -> LoadedSkillsBundle | None:
    if line is None:
        return None
    bundle_ref = str(line.skills_bundle_ref or "").strip()
    if not bundle_ref:
        return None
    return _load_bundle(bundle_ref, line.line_id)


def run_loaded_skills_bundle(
    bundle: LoadedSkillsBundle,
    payload: dict[str, Any],
) -> dict[str, Any]:
    stage_results: dict[str, dict[str, Any]] = {}
    for stage in bundle.stage_order:
        runner = bundle.stage_runners.get(stage)
        if runner is None:
            continue
        result = runner(
            payload,
            defaults=bundle.defaults,
            stage_results=dict(stage_results),
        )
        if result is None:
            continue
        if isinstance(result, dict):
            stage_results[stage] = dict(result)
        else:
            stage_results[stage] = {"value": result}
    return {
        "bundle_id": bundle.bundle_id,
        "line_id": bundle.line_id,
        "bundle_ref": bundle.bundle_ref,
        "hook_kind": bundle.hook_kind,
        "stage_order": list(bundle.stage_order),
        "stage_results": stage_results,
    }

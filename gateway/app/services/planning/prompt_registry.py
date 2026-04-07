from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


SCRIPT_VIDEO_PROMPT_REGISTRY_REF = "gateway/app/prompts/script_video_planning_defaults.yaml"


@dataclass(frozen=True)
class PromptTemplateSpec:
    template_id: str
    line_id: str
    category: str
    family: str
    variant: str
    description: str
    system_prompt: str
    is_default: bool = False


@dataclass(frozen=True)
class PlanningPromptRegistry:
    line_id: str
    registry_ref: str
    templates: tuple[PromptTemplateSpec, ...]

    def resolve(self, template_id: str | None) -> PromptTemplateSpec | None:
        wanted = str(template_id or "").strip()
        if not wanted:
            return None
        for template in self.templates:
            if template.template_id == wanted:
                return template
        return None

    def resolve_default(
        self,
        *,
        category: str,
        family: str | None = None,
    ) -> PromptTemplateSpec | None:
        wanted_category = str(category or "").strip()
        wanted_family = str(family or "").strip() or None
        candidates = [
            template
            for template in self.templates
            if template.category == wanted_category and (wanted_family is None or template.family == wanted_family)
        ]
        if not candidates:
            return None
        for template in candidates:
            if template.is_default:
                return template
        return candidates[0]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=8)
def load_planning_prompt_registry(registry_ref: str = SCRIPT_VIDEO_PROMPT_REGISTRY_REF) -> PlanningPromptRegistry:
    path = (_repo_root() / registry_ref).resolve()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    line_id = str(payload.get("line_id") or "script_video_line").strip() or "script_video_line"
    templates: list[PromptTemplateSpec] = []
    for family_payload in payload.get("families") or []:
        category = str(family_payload.get("category") or "").strip()
        family = str(family_payload.get("family") or "").strip()
        default_variant = str(family_payload.get("default_variant") or "").strip() or None
        for template_payload in family_payload.get("templates") or []:
            variant = str(template_payload.get("variant") or "").strip() or "default"
            templates.append(
                PromptTemplateSpec(
                    template_id=str(template_payload.get("template_id") or "").strip(),
                    line_id=line_id,
                    category=category,
                    family=family,
                    variant=variant,
                    description=str(template_payload.get("description") or "").strip(),
                    system_prompt=str(template_payload.get("system_prompt") or ""),
                    is_default=(default_variant == variant),
                )
            )
    return PlanningPromptRegistry(
        line_id=line_id,
        registry_ref=registry_ref,
        templates=tuple(templates),
    )

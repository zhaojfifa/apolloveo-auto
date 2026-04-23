from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .runtime_loader import load_markdown_yaml_sections


@dataclass(frozen=True)
class BlockingReasonRuntime:
    ref: str
    maps: dict[str, str]
    non_blocking: dict[str, str]
    aliases: dict[str, str]
    metadata: dict[str, dict[str, Any]]

    def canonicalize(self, reason: str | None) -> str:
        raw = str(reason or "").strip()
        if not raw:
            return ""
        aliased = self.aliases.get(raw, raw)
        return self.maps.get(aliased, aliased)

    def normalize_list(self, reasons: list[str] | tuple[str, ...] | None) -> list[str]:
        normalized: list[str] = []
        for reason in reasons or []:
            canonical = self.canonicalize(reason)
            if canonical and canonical not in normalized:
                normalized.append(canonical)
        return normalized

    def is_non_blocking(self, reason: str | None) -> bool:
        canonical = self.canonicalize(reason)
        meta = self.metadata.get(canonical) or {}
        return meta.get("class") == "advisory" or canonical in self.non_blocking

    def suppress_when_publish_ready(self, reason: str | None) -> bool:
        canonical = self.canonicalize(reason)
        meta = self.metadata.get(canonical) or {}
        return bool(meta.get("suppress_when_publish_ready"))

    def scene_pack_pending_reason(self, status: str | None) -> str | None:
        normalized = str(status or "").strip().lower()
        if normalized == "running":
            return self.canonicalize("scenes.running")
        if normalized == "failed":
            return self.canonicalize("scenes.failed")
        if normalized:
            return self.canonicalize("scenes_not_ready")
        return self.canonicalize("scenes_not_ready")


@lru_cache(maxsize=16)
def get_blocking_reason_runtime(ref: str) -> BlockingReasonRuntime:
    sections = load_markdown_yaml_sections(ref)
    payload = sections.get("blocking_reason_mapping_contract") or {}
    if not isinstance(payload, dict):
        raise RuntimeError(f"missing blocking_reason_mapping_contract in {ref}")
    maps = payload.get("maps") or {}
    non_blocking = payload.get("non_blocking") or {}
    aliases = payload.get("aliases") or {}
    metadata = payload.get("metadata") or {}
    return BlockingReasonRuntime(
        ref=ref,
        maps={str(k): str(v) for k, v in maps.items()},
        non_blocking={str(k): str(v) for k, v in non_blocking.items()},
        aliases={str(k): str(v) for k, v in aliases.items()},
        metadata={
            str(k): (v if isinstance(v, dict) else {})
            for k, v in metadata.items()
        },
    )


def filter_publish_ready_blocking(
    reasons: list[str] | tuple[str, ...] | None,
    runtime: BlockingReasonRuntime,
) -> list[str]:
    filtered: list[str] = []
    for reason in runtime.normalize_list(reasons):
        if runtime.is_non_blocking(reason):
            continue
        if runtime.suppress_when_publish_ready(reason):
            continue
        filtered.append(reason)
    return filtered


def scene_pack_pending_reason(
    status: str | None,
    runtime: BlockingReasonRuntime,
) -> str | None:
    return runtime.scene_pack_pending_reason(status)

"""Minimal env-backed ``SecretResolver`` (W2.1 first provider absorption).

Constraints (frozen for this wave):

- Resolution is **invocation-time only**. Construction stores the
  ``logical_name -> env_var_name`` mapping; no env reads happen at
  ``__init__``. This preserves the B1 / B4 lifecycle boundary at the
  AdapterBase layer.
- Reads canonical env names only. Aliases (e.g. ``GOOGLE_API_KEY`` for
  ``GEMINI_API_KEY``) MUST NOT be added here per
  ``ops/env/secret_loading_baseline_v1.md`` §3.1.
- Returns ``None`` when the env var is missing or empty after strip;
  fail-closed semantics belong to the caller (the adapter binding) per
  ``ops/env/secret_loading_baseline_v1.md`` §3.5.
- Carries no logger, no cache, no platform expansion. This is a shim,
  not a generic secrets framework.
"""
from __future__ import annotations

import os
from types import MappingProxyType
from typing import Mapping, Optional

from gateway.app.services.capability.adapters import (
    SecretRef,
    SecretResolver,
)


class EnvSecretResolver(SecretResolver):
    """Resolve ``SecretRef.name`` via a frozen logical→env-var mapping.

    The mapping is supplied by the adapter binding (which knows which
    canonical env names belong to its provider) and is the only
    construction-time input. Resolution itself happens at invoke-time.
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: Mapping[str, str]) -> None:
        if not isinstance(mapping, Mapping):
            raise TypeError("mapping must be a Mapping[str, str]")
        normalised: dict[str, str] = {}
        for key, value in mapping.items():
            if not isinstance(key, str) or not key:
                raise ValueError(
                    "EnvSecretResolver mapping keys must be non-empty strings"
                )
            if not isinstance(value, str) or not value:
                raise ValueError(
                    "EnvSecretResolver mapping values must be non-empty "
                    "env var names"
                )
            normalised[key] = value
        self._mapping: Mapping[str, str] = MappingProxyType(normalised)

    @property
    def mapping(self) -> Mapping[str, str]:
        """Read-only view of the logical→env-var mapping."""
        return self._mapping

    def resolve(self, ref: SecretRef) -> Optional[str]:
        if not isinstance(ref, SecretRef):
            raise TypeError("ref must be a SecretRef")
        env_name = self._mapping.get(ref.name)
        if env_name is None:
            return None
        value = os.environ.get(env_name)
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

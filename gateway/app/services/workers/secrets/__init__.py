"""Worker-side secret resolver shims (W2.1 first provider absorption).

Concrete ``SecretResolver`` implementations for use by worker-side adapter
bindings. Lives outside ``gateway/app/services/capability/adapters/`` per
B1 boundary discipline (the AdapterBase package never grows a dependency
on env / vault loaders).

Scope is intentionally narrow for W2.1: only what the first provider
absorption (UnderstandingAdapter ← Gemini text translate) needs.
"""
from .env_resolver import EnvSecretResolver

__all__ = ["EnvSecretResolver"]

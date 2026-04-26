"""W2 admission guardrail — provider SDK leak / import boundary.

Authority:
- `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
  §4 Phase A, §7 (forbidden actions)
- `docs/donor/swiftcraft_donor_boundary_v1.md` §5.5 (Adapter binding rule),
  §7 (Front-end isolation)
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.4

Rule:
    Provider SDKs MAY only appear inside explicit adapter / provider zones.
    Frontstage/UI zones and domain/truth zones MUST NOT import provider
    SDKs (e.g. `openai`, `azure.cognitiveservices.*`, `fal_client`,
    `elevenlabs`, `anthropic`). Any provider call from a forbidden zone
    must go through a capability adapter.

This is the FIRST line of defense for W2: before any provider SDK lands,
this test must already be enforced so a careless import in `web/` or
`packet/` fails CI immediately.
"""
from __future__ import annotations

from pathlib import Path

from tests.guardrails._scan import REPO_ROOT, find_forbidden


# Zones where importing a provider SDK is FORBIDDEN.
FORBIDDEN_ZONES = [
    # Frontstage / UI
    REPO_ROOT / "gateway" / "app" / "web",
    # Domain truth
    REPO_ROOT / "gateway" / "app" / "domain",
    # Truth-authority runtimes
    REPO_ROOT / "gateway" / "app" / "services" / "contract_runtime",
    REPO_ROOT / "gateway" / "app" / "services" / "ready_gate",
    REPO_ROOT / "gateway" / "app" / "services" / "packet",
]

# Top-level provider SDK names. Match by AST import target, not substring,
# so unrelated tokens in docstrings or string literals are ignored.
FORBIDDEN_PROVIDER_SDKS = {
    "openai",
    "azure.cognitiveservices",
    "azure.cognitiveservices.speech",
    "fal_client",
    "elevenlabs",
    "anthropic",
    "google.cloud.speech",
    "google.cloud.texttospeech",
    "boto3",  # storage provider SDK; must live behind storage adapter
}


def test_no_provider_sdk_import_in_forbidden_zones():
    hits = find_forbidden(FORBIDDEN_ZONES, FORBIDDEN_PROVIDER_SDKS)
    assert not hits, _format_hits(
        "Provider SDK imported in a forbidden zone (frontstage/UI or "
        "domain/truth). Provider calls must go through a capability adapter.",
        hits,
    )


def test_forbidden_zones_actually_exist():
    """Sanity: at least one zone must exist; otherwise the test is vacuous.

    If the repo layout is reorganized and these directories disappear, the
    guardrail must be re-pointed before silently passing.
    """
    existing = [z for z in FORBIDDEN_ZONES if z.exists()]
    assert existing, (
        "None of the forbidden zones exist on disk. The guardrail's zone "
        "list is stale and must be updated before it can protect anything."
    )


def _format_hits(header: str, hits: list[tuple[Path, str]]) -> str:
    lines = [header, ""]
    for path, name in sorted({(p.relative_to(REPO_ROOT), n) for p, n in hits}):
        lines.append(f"  - {path}: imports `{name}`")
    return "\n".join(lines)

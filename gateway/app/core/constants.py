"""Shared constants and lightweight request models for the gateway routers.

Extracted from tasks.py as part of Phase 1.3 Port Merge.
"""
from typing import Optional

from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

# ── Auth / Ops ───────────────────────────────────────────────────────────────
OP_HEADER_KEY = "X-OP-KEY"
api_key_header = APIKeyHeader(name=OP_HEADER_KEY, auto_error=False)

# ── Compose ──────────────────────────────────────────────────────────────────
COMPOSE_RETRY_AFTER_MS = 1500


# ── Shared Pydantic request models ───────────────────────────────────────────
class DubProviderRequest(BaseModel):
    provider: Optional[str] = None
    voice_id: Optional[str] = None
    mm_text: Optional[str] = None
    tts_speed: Optional[float] = None
    force: bool = False


class PublishBackfillRequest(BaseModel):
    publish_url: Optional[str] = None
    note: Optional[str] = None
    status: Optional[str] = None

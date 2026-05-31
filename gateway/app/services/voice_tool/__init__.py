"""Standalone Voice Translation Tool service package.

This package is intentionally isolated from production-line runtime code.
"""

from .service import (
    VoiceToolError,
    VoiceToolService,
    get_voice_tool_service,
)

__all__ = ["VoiceToolError", "VoiceToolService", "get_voice_tool_service"]

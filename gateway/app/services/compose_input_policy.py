from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SOFT_MAX_BYTES = 80 * 1024 * 1024
HARD_MAX_BYTES = 250 * 1024 * 1024
MAX_DURATION_SEC = 300.0
MAX_VIDEO_BITRATE = 8_000_000
DIRECT_PIXEL_BUDGET = 1920 * 1080
HARD_PIXEL_BUDGET = 2560 * 1440
MIN_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class ComposeInputProfile:
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    video_bitrate: int | None = None
    free_disk_bytes: int | None = None

    @property
    def pixels(self) -> int | None:
        if self.width is None or self.height is None:
            return None
        return int(self.width) * int(self.height)

    @property
    def orientation(self) -> str | None:
        if self.width is None or self.height is None:
            return None
        if self.height > self.width:
            return "portrait"
        if self.width > self.height:
            return "landscape"
        return "square"

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "duration_sec": self.duration_sec,
            "video_bitrate": self.video_bitrate,
            "free_disk_bytes": self.free_disk_bytes,
            "pixels": self.pixels,
            "orientation": self.orientation,
        }


@dataclass(frozen=True)
class ComposeInputPolicyDecision:
    mode: str
    reason: str | None = None
    profile: ComposeInputProfile | None = None

    @property
    def blocked(self) -> bool:
        return self.mode == "blocked"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reason": self.reason,
            "profile": self.profile.to_dict() if self.profile else None,
        }


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or str(value).strip().upper() == "N/A":
            return None
        return int(float(value))
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip().upper() == "N/A":
            return None
        return float(value)
    except Exception:
        return None


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def compose_input_profile_from_task(task: dict[str, Any] | None) -> ComposeInputProfile | None:
    task = task or {}
    compose = task.get("compose") if isinstance(task.get("compose"), dict) else {}
    probe = _first_mapping(
        task.get("compose_input_probe"),
        compose.get("input_probe"),
        task.get("source_video_profile"),
        task.get("video_profile"),
    )
    if not probe:
        return None
    width = _safe_int(probe.get("width"))
    height = _safe_int(probe.get("height"))
    file_size = _safe_int(probe.get("file_size_bytes") or probe.get("size_bytes"))
    duration = _safe_float(probe.get("duration_sec") or probe.get("duration"))
    bitrate = _safe_int(probe.get("video_bitrate") or probe.get("bit_rate"))
    free_disk = _safe_int(probe.get("free_disk_bytes"))
    if not any(v is not None for v in (width, height, file_size, duration, bitrate, free_disk)):
        return None
    return ComposeInputProfile(
        width=width,
        height=height,
        file_size_bytes=file_size,
        duration_sec=duration,
        video_bitrate=bitrate,
        free_disk_bytes=free_disk,
    )


def evaluate_compose_input_policy(task: dict[str, Any] | None) -> ComposeInputPolicyDecision:
    profile = compose_input_profile_from_task(task)
    if profile is None:
        return ComposeInputPolicyDecision(mode="direct", reason=None, profile=None)

    pixels = profile.pixels
    if profile.free_disk_bytes is not None and profile.free_disk_bytes < MIN_FREE_DISK_BYTES:
        return ComposeInputPolicyDecision("blocked", "disk_insufficient", profile)
    if profile.file_size_bytes is not None and profile.file_size_bytes > HARD_MAX_BYTES:
        return ComposeInputPolicyDecision("blocked", "input_too_large", profile)
    if profile.duration_sec is not None and profile.duration_sec > MAX_DURATION_SEC:
        return ComposeInputPolicyDecision("blocked", "duration_too_long", profile)
    if profile.video_bitrate is not None and profile.video_bitrate > MAX_VIDEO_BITRATE:
        return ComposeInputPolicyDecision("blocked", "bitrate_too_high", profile)
    if pixels is not None and pixels > HARD_PIXEL_BUDGET:
        return ComposeInputPolicyDecision("blocked", "resolution_too_high", profile)

    if (
        profile.file_size_bytes is not None
        and profile.file_size_bytes > SOFT_MAX_BYTES
        and pixels is not None
        and pixels > DIRECT_PIXEL_BUDGET
    ):
        return ComposeInputPolicyDecision("blocked", "input_requires_hardening", profile)

    return ComposeInputPolicyDecision("direct", None, profile)


def build_compose_input_block_updates(decision: ComposeInputPolicyDecision) -> dict[str, Any]:
    reason = decision.reason or "compose_input_blocked"
    message = f"compose input blocked before compose execution: {reason}"
    return {
        "compose_status": "blocked",
        "compose_last_status": "blocked",
        "compose_last_finished_at": None,
        "compose_last_error": message,
        "compose_error_reason": reason,
        "compose_error": {"reason": reason, "message": message},
        "compose_allowed": False,
        "compose_allowed_reason": reason,
        "compose_input_policy": decision.to_dict(),
        "compose_lock_until": None,
    }


def build_compose_input_direct_updates() -> dict[str, Any]:
    return {
        "compose_allowed": None,
        "compose_allowed_reason": None,
        "compose_input_policy": None,
    }


def stale_compose_input_policy_updates(task: dict[str, Any] | None) -> dict[str, Any]:
    task = task or {}
    if not isinstance(task.get("compose_input_policy"), dict):
        return {}
    updates = build_compose_input_direct_updates()
    if str(task.get("compose_status") or "").strip().lower() == "blocked":
        updates.update(
            {
                "compose_status": "pending",
                "compose_last_status": "pending",
                "compose_last_error": None,
                "compose_error_reason": None,
                "compose_error": None,
                "compose_lock_until": None,
            }
        )
    return updates

"""Hot Follow-owned media input and subtitle style policy.

This module is deliberately narrow: it centralizes the contract values needed
by upload ingress, compose-time safe media derivation, output quality targeting,
and burned-subtitle styling without introducing provider or line expansion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HotFollowMediaInputPolicy:
    max_upload_size_mb: int = 300
    accepted_input_types: tuple[str, ...] = ("video/mp4", "video/quicktime", "video/x-matroska")
    accepted_extensions: tuple[str, ...] = (".mp4", ".mov", ".mkv")
    quality_tier_default: str = "source_preserving_720p_1080p"
    target_output_band: str = "720p_1080p"
    prefer_source_quality_preservation: bool = True
    oversize_handling_policy: str = "preserve_original_and_derive_runtime_safe_compose_asset"
    derive_min_size_mb: int = 250
    derive_min_bitrate: int = 12_000_000
    derive_min_pixels: int = 1920 * 1080
    target_short_edge_max: int = 1080
    target_long_edge_max: int = 1920
    target_short_edge_floor: int = 720
    derive_crf: int = 21

    @property
    def max_upload_size_bytes(self) -> int:
        return int(self.max_upload_size_mb) * 1024 * 1024

    @property
    def derive_min_bytes(self) -> int:
        return int(self.derive_min_size_mb) * 1024 * 1024

    def accepts_filename(self, filename: str | None) -> bool:
        return Path(str(filename or "")).suffix.lower() in self.accepted_extensions

    def to_contract_dict(self) -> dict[str, Any]:
        return {
            "max_upload_size_mb": self.max_upload_size_mb,
            "accepted_input_types": list(self.accepted_input_types),
            "quality_tier_default": self.quality_tier_default,
            "target_output_band": self.target_output_band,
            "prefer_source_quality_preservation": self.prefer_source_quality_preservation,
            "oversize_handling_policy": self.oversize_handling_policy,
            "derive_min_size_mb": self.derive_min_size_mb,
            "derive_min_bitrate": self.derive_min_bitrate,
            "derive_min_pixels": self.derive_min_pixels,
            "target_short_edge_max": self.target_short_edge_max,
            "target_long_edge_max": self.target_long_edge_max,
            "target_short_edge_floor": self.target_short_edge_floor,
            "derive_crf": self.derive_crf,
        }


@dataclass(frozen=True)
class HotFollowSubtitleStyleProfile:
    subtitle_style_profile: str
    font_name: str
    font_size: float
    margin_v: int
    line_width: float
    line_spacing: float = 0.0
    alignment: int = 2
    wrap_style: int = 1
    safe_margin_behavior: str = "preserve_existing_bottom_safe_area"

    def font_size_ass(self) -> str:
        return f"{float(self.font_size):.1f}"

    def to_signature_parts(self, *, lang: str, cleanup: str) -> list[str]:
        return [
            f"profile={self.subtitle_style_profile}",
            f"lang={lang}",
            f"cleanup={cleanup}",
            f"font={self.font_name}",
            f"size={self.font_size_ass()}",
            f"margin_v={int(self.margin_v)}",
            f"line_width={float(self.line_width):.2f}",
            f"line_spacing={float(self.line_spacing):.1f}",
            f"safe_margin={self.safe_margin_behavior}",
            f"align={int(self.alignment)}",
            f"wrap={int(self.wrap_style)}",
        ]


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except Exception:
        return default
    return value if value > 0 else default


def hot_follow_media_input_policy() -> HotFollowMediaInputPolicy:
    return HotFollowMediaInputPolicy(
        max_upload_size_mb=_env_int("HF_MAX_UPLOAD_SIZE_MB", 300),
        derive_min_size_mb=_env_int("HF_COMPOSE_DERIVE_MIN_MB", 250),
        derive_min_bitrate=_env_int("HF_COMPOSE_DERIVE_MIN_BITRATE", 12_000_000),
        derive_min_pixels=_env_int("HF_COMPOSE_DERIVE_MIN_PIXELS", 1920 * 1080),
        target_short_edge_max=_env_int("HF_OUTPUT_TARGET_SHORT_EDGE_MAX", 1080),
        target_long_edge_max=_env_int("HF_OUTPUT_TARGET_LONG_EDGE_MAX", 1920),
        target_short_edge_floor=_env_int("HF_OUTPUT_TARGET_SHORT_EDGE_FLOOR", 720),
        derive_crf=_env_int("HF_COMPOSE_DERIVE_CRF", 21),
    )


def hot_follow_local_upload_source_selection_guard(
    *,
    filename: str | None,
    title: str | None,
    source_audio_policy: str | None,
) -> dict[str, Any]:
    """Block obvious lyric/BGM assets from being selected as preserved source audio."""
    policy = str(source_audio_policy or "").strip().lower()
    if policy != "preserve":
        return {"allow": True, "reason": None}
    label = f"{filename or ''} {title or ''}".lower()
    lyric_bgm_markers = (
        "lyric",
        "lyrics",
        "karaoke",
        "bgm",
        "music",
        "instrumental",
        "歌词",
        "字幕歌",
        "卡拉ok",
        "伴奏",
        "配乐",
        "音乐",
    )
    if any(marker in label for marker in lyric_bgm_markers):
        return {
            "allow": False,
            "reason": "local_upload_lyric_bgm_source_audio_misselection",
            "message": "Local lyric/BGM material cannot be selected as preserved source audio for Hot Follow dubbing.",
        }
    return {"allow": True, "reason": None}


def hot_follow_compose_scale_expr(policy: HotFollowMediaInputPolicy | None = None) -> str:
    """Return orientation-aware 720p-1080p-band derive scaling for FFmpeg."""
    current = policy or hot_follow_media_input_policy()
    short_max = int(current.target_short_edge_max)
    long_max = int(current.target_long_edge_max)
    return (
        f"scale='min(iw,if(gte(iw,ih),{long_max},{short_max}))':"
        f"'min(ih,if(gte(iw,ih),{short_max},{long_max}))':"
        "force_original_aspect_ratio=decrease:force_divisible_by=2"
    )


def normalize_hot_follow_layout_lang(target_lang: str | None) -> str:
    raw = str(target_lang or "").strip().lower()
    if raw == "mm":
        return "my"
    return raw or "my"


def hot_follow_subtitle_style_profile(target_lang: str | None) -> HotFollowSubtitleStyleProfile:
    lang = normalize_hot_follow_layout_lang(target_lang)
    if lang == "zh":
        return HotFollowSubtitleStyleProfile(
            subtitle_style_profile="hot_follow_compact_default",
            font_name="Noto Sans Myanmar",
            font_size=14.0,
            margin_v=18,
            line_width=11.5,
        )
    if lang == "en":
        return HotFollowSubtitleStyleProfile(
            subtitle_style_profile="hot_follow_compact_default",
            font_name="Noto Sans Myanmar",
            font_size=13.2,
            margin_v=18,
            line_width=24.0,
        )
    if lang == "vi":
        return HotFollowSubtitleStyleProfile(
            subtitle_style_profile="hot_follow_compact_default",
            font_name="Noto Sans Myanmar",
            font_size=13.2,
            margin_v=18,
            line_width=22.0,
        )
    return HotFollowSubtitleStyleProfile(
        subtitle_style_profile="hot_follow_compact_default",
        font_name="Noto Sans Myanmar",
        font_size=14.0,
        margin_v=18,
        line_width=13.0,
    )

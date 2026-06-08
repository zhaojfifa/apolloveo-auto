"""Matrix Script Akool image_to_video capability — real provider one-shot.

Wires the real Akool ``image_to_video`` capability into the Matrix Script production
path as a **backend capability provider** (capability kind = ``image_to_video``), NOT
a UI vendor selector. It performs a genuine one-shot generation for a single shot:

    local still  → host as a temporary URL (Apollo artifact storage)
                 → Akool create_task(IMAGE_TO_VIDEO, {image_url, prompt})
                 → bounded poll read_task_result until SUCCESS / FAILED / timeout
                 → download the provider's temporary output to a local mp4
                 → normalise to the backbone spec (1080×1920 / 30fps h264)
                 → return a per-shot result with an HONEST status.

Default OFF: a real call happens only when ``MATRIX_SCRIPT_AKOOL_REAL`` is truthy AND
the ``AKOOL_API_KEY`` secret resolves. Otherwise the caller keeps the local backbone
fallback and the status reports the honest reason (never a fake provider clip).

Hard boundary:
- The api key lives only on the outgoing request header (built by ``AkoolClient``); it
  is NEVER returned, logged, written to a manifest, or surfaced in operator copy.
- No provider URL / task id / vendor / model / credit / secret in any returned field —
  only a closed status enum + a provider-agnostic operator label + a redacted error
  CLASS name for diagnostics.
- ``official_publish_ready`` is unaffected (stays false); this produces a preview clip.
- Transport / hoster / downloader are injectable so tests never touch the network.
"""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from gateway.app.services.matrix_script import ffmpeg_backbone as backbone
from gateway.app.services.matrix_script.akool_real_gate import AKOOL_REAL_FLAG_ENV
from gateway.app.services.providers.akool import (
    AkoolCapability,
    AkoolClient,
    AkoolClientConfig,
    AkoolError,
    AkoolErrorKind,
    AkoolHttpRequest,
    AkoolHttpResponse,
    AkoolTaskStatus,
)
from gateway.app.services.workers.adapters.akool import (
    AKOOL_API_KEY_REF,
    AKOOL_BASE_URL_REF,
    AKOOL_LOGICAL_TO_ENV,
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})

# Closed per-shot status taxonomy (operator-facing; no vendor string).
STATUS_PROVIDER_SUCCESS = "provider_success"
STATUS_PROVIDER_FAILED = "provider_failed"
STATUS_CREDENTIAL_MISSING = "credential_missing"
STATUS_POLICY_BLOCKED = "policy_blocked"
STATUS_TIMEOUT = "timeout"
STATUS_FALLBACK_USED = "fallback_used"

_OPERATOR_LABEL = {
    STATUS_PROVIDER_SUCCESS: "AI 视频生成已生成此镜头",
    STATUS_PROVIDER_FAILED: "AI 视频生成未成功 · 已回退本地兜底",
    STATUS_CREDENTIAL_MISSING: "AI 视频生成未启用 · 缺少凭证（使用本地兜底）",
    STATUS_POLICY_BLOCKED: "AI 视频生成被服务限制 · 已回退本地兜底",
    STATUS_TIMEOUT: "AI 视频生成超时 · 已回退本地兜底",
    STATUS_FALLBACK_USED: "本镜头使用本地兜底生成",
}

# Akool error kind → honest status (no vendor message surfaced).
_KIND_TO_STATUS = {
    AkoolErrorKind.AUTH: STATUS_CREDENTIAL_MISSING,
    AkoolErrorKind.QUOTA: STATUS_POLICY_BLOCKED,
    AkoolErrorKind.RATE_LIMITED: STATUS_POLICY_BLOCKED,
    AkoolErrorKind.TIMEOUT: STATUS_TIMEOUT,
}

DEFAULT_PROMPT = "subtle natural camera motion, gentle parallax, realistic lighting"


@dataclass(frozen=True)
class AkoolShotResult:
    """Per-shot Akool one-shot outcome — honest status, no provider/secret leak."""

    status: str
    clip_path: Optional[str] = None
    provider_attempted: bool = False
    redacted_detail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status == STATUS_PROVIDER_SUCCESS and bool(self.clip_path)

    @property
    def operator_label_zh(self) -> str:
        return _OPERATOR_LABEL.get(self.status, "AI 视频生成状态未知")

    def to_status_dict(self) -> dict:
        return {
            "capability": "image_to_video",
            "status": self.status,
            "provider_attempted": self.provider_attempted,
            "succeeded": self.succeeded,
            "operator_label_zh": self.operator_label_zh,
        }


def real_enabled(env: Optional[Mapping[str, str]] = None) -> bool:
    src = env if env is not None else os.environ
    return str(src.get(AKOOL_REAL_FLAG_ENV, "")).strip().lower() in _TRUTHY


_API_KEY_ENV = AKOOL_LOGICAL_TO_ENV[AKOOL_API_KEY_REF.name]
_BASE_URL_ENV = AKOOL_LOGICAL_TO_ENV[AKOOL_BASE_URL_REF.name]


def _resolve_akool_env(env: Optional[Mapping[str, str]]):
    """Resolve (api_key, base_url) from the canonical logical→env mapping.

    Honors an explicitly-passed ``env`` mapping (for tests) and falls back to the
    process environment (the real run after ``source``-ing the env file).
    """
    src = env if env is not None else os.environ
    api_key = (src.get(_API_KEY_ENV) or "").strip()
    base_url = (src.get(_BASE_URL_ENV) or "").strip()
    return api_key, base_url


def credentials_present(env: Optional[Mapping[str, str]] = None) -> bool:
    api_key, _ = _resolve_akool_env(env)
    return bool(api_key)


def _httpx_transport(request: AkoolHttpRequest) -> AkoolHttpResponse:
    """Real HTTP transport for the Akool client (no secret logged)."""
    import httpx

    with httpx.Client(timeout=httpx.Timeout(30.0, connect=15.0)) as client:
        if request.method == "POST":
            resp = client.post(request.url, headers=dict(request.headers), json=request.json_body)
        elif request.method == "GET":
            resp = client.get(request.url, headers=dict(request.headers), params=dict(request.query or {}))
        else:
            raise AkoolError(AkoolErrorKind.PROTOCOL, "unsupported method")
        try:
            body = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise AkoolError(AkoolErrorKind.PROTOCOL, "non-json response") from exc
    return AkoolHttpResponse(status_code=resp.status_code, body=body)


def _default_host_image(task_id: str, shot_id: str, local_path: str) -> str:
    """Host a local still as a temporary URL via Apollo artifact storage (R2/local)."""
    from gateway.app.services import artifact_storage

    name = f"akool_src_{shot_id}{os.path.splitext(local_path)[1] or '.png'}"
    key = artifact_storage.upload_artifact(task_id, local_path, name)
    return artifact_storage.get_download_url(key)


def _default_download(url: str, out_path: str) -> None:
    import httpx

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with httpx.Client(timeout=httpx.Timeout(120.0, connect=15.0), follow_redirects=True) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as fh:
                for chunk in resp.iter_bytes():
                    fh.write(chunk)


def _normalize_to_backbone_spec(in_path: str, out_path: str) -> None:
    """Re-encode a provider clip to the deterministic backbone spec for clean concat."""
    vf = (
        f"scale={backbone.BACKBONE_WIDTH}:{backbone.BACKBONE_HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={backbone.BACKBONE_WIDTH}:{backbone.BACKBONE_HEIGHT},fps={backbone.BACKBONE_FPS}"
    )
    cmd = [
        backbone.ffmpeg_path() or "ffmpeg", "-y", "-i", in_path, "-vf", vf,
        "-c:v", backbone.BACKBONE_VENCODER, "-preset", backbone.BACKBONE_PRESET,
        "-crf", backbone.BACKBONE_CRF, "-pix_fmt", backbone.BACKBONE_PIX_FMT, "-an", out_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
    if proc.returncode != 0 or not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
        raise RuntimeError("normalize failed")


def generate_shot_clip_akool(
    *,
    still_path: str,
    out_clip: str,
    task_id: str,
    shot_id: str,
    prompt: str = DEFAULT_PROMPT,
    env: Optional[Mapping[str, str]] = None,
    transport: Optional[Callable[[AkoolHttpRequest], AkoolHttpResponse]] = None,
    host_image: Optional[Callable[[str, str, str], str]] = None,
    download: Optional[Callable[[str, str], None]] = None,
    poll_max_seconds: float = 90.0,
    poll_interval_seconds: float = 8.0,
) -> AkoolShotResult:
    """Attempt a real Akool image_to_video one-shot for a single shot.

    Returns an :class:`AkoolShotResult` with an honest status. Never raises for a
    provider/credential/policy/timeout problem — those degrade to a status so the
    caller keeps the local fallback. Injectable ``transport`` / ``host_image`` /
    ``download`` keep the path unit-testable without network or secrets.
    """
    src = env if env is not None else os.environ
    if not real_enabled(src):
        return AkoolShotResult(STATUS_CREDENTIAL_MISSING, None, False, "flag_off")
    api_key, base_url = _resolve_akool_env(src)
    if not api_key:
        return AkoolShotResult(STATUS_CREDENTIAL_MISSING, None, False, "no_api_key")

    transport = transport or _httpx_transport
    host_image = host_image or _default_host_image
    download = download or _default_download

    try:
        config = AkoolClientConfig(api_key=api_key, base_url=base_url or AkoolClientConfig.base_url)
    except ValueError:
        config = AkoolClientConfig(api_key=api_key)
    client = AkoolClient(config, transport=transport)

    try:
        image_url = host_image(task_id, shot_id, still_path)
        created = client.create_task(
            AkoolCapability.IMAGE_TO_VIDEO, {"image_url": image_url, "prompt": prompt}
        )
        deadline = time.monotonic() + float(poll_max_seconds)
        output_url: Optional[str] = None
        while True:
            read = client.read_task_result(AkoolCapability.IMAGE_TO_VIDEO, created.provider_task_id)
            if read.status is AkoolTaskStatus.SUCCESS:
                output_url = read.output.url if read.output else None
                break
            if read.status is AkoolTaskStatus.FAILED:
                return AkoolShotResult(STATUS_PROVIDER_FAILED, None, True, "provider_status_failed")
            if time.monotonic() >= deadline:
                return AkoolShotResult(STATUS_TIMEOUT, None, True, "poll_timeout")
            time.sleep(float(poll_interval_seconds))
        if not output_url:
            return AkoolShotResult(STATUS_PROVIDER_FAILED, None, True, "success_no_output")
    except AkoolError as exc:
        status = _KIND_TO_STATUS.get(exc.kind, STATUS_PROVIDER_FAILED)
        return AkoolShotResult(status, None, True, f"provider:{exc.kind.name.lower()}")
    except Exception as exc:  # noqa: BLE001 — host/transport/etc.; redacted class only
        return AkoolShotResult(STATUS_PROVIDER_FAILED, None, True, f"err:{exc.__class__.__name__}")

    # Download + normalise the provider output into a local backbone-spec clip.
    try:
        raw = out_clip + ".akool_raw.mp4"
        download(output_url, raw)
        if not (os.path.exists(raw) and os.path.getsize(raw) > 0):
            return AkoolShotResult(STATUS_PROVIDER_FAILED, None, True, "download_empty")
        _normalize_to_backbone_spec(raw, out_clip)
    except Exception as exc:  # noqa: BLE001
        return AkoolShotResult(STATUS_PROVIDER_FAILED, None, True, f"postproc:{exc.__class__.__name__}")

    return AkoolShotResult(STATUS_PROVIDER_SUCCESS, out_clip, True, "")

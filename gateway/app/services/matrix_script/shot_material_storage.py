"""Matrix Script P1-3 PR-C — Shot material upload / storage handle.

Stores an operator-uploaded shot material file under a Matrix-Script-scoped
*local workspace* path and returns a resolvable handle. This upgrades a shot's
attached material from a bare operator reference (``asset://...``, PR-A) to a
handle whose BYTES are resolvable (``bytes_resolvable=true``).

Boundary: this makes bytes *resolvable*, it does NOT make V2 regeneration
*consume* them — that is PR-D (``material_bytes_consumed`` stays false). No
``artifact_storage.py`` / provider / schema-contract / publish surface is
touched; the handle is an internal local reference, never a public publish URL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from gateway.app.config import get_settings

# Storage facts recorded on the shot intent entry (operator-safe vocabulary).
STORAGE_SCOPE_LOCAL = "local_workspace"
MATERIAL_SOURCE_UPLOAD = "operator_upload"

# Operator-safe handle scheme for a stored shot material file. Resolvable to
# local bytes by this storage layer only; NOT a provider/publish URL.
MATERIAL_HANDLE_SCHEME = "msmaterial://"

KIND_IMAGE = "image"
KIND_VIDEO = "video"
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_VIDEO_EXTS = {".mp4", ".mov", ".webm"}

DEFAULT_MAX_MB = 50


class ShotMaterialStorageError(ValueError):
    """Raised on an unsafe / invalid shot material upload."""


@dataclass(frozen=True)
class StoredShotMaterial:
    shot_id: str
    material_kind: str
    material_name: str
    local_path: str
    material_ref: str          # msmaterial://<task_id>/<shot_id>/<filename>
    preview_url: str           # /api/matrix-script/<task_id>/shot-material/<shot_id>/file
    storage_scope: str = STORAGE_SCOPE_LOCAL
    material_source: str = MATERIAL_SOURCE_UPLOAD
    bytes_resolvable: bool = True


def material_kind_for_ext(ext: str) -> Optional[str]:
    e = (ext or "").lower()
    if e in _IMAGE_EXTS:
        return KIND_IMAGE
    if e in _VIDEO_EXTS:
        return KIND_VIDEO
    return None


def _material_root(task_id: str, shot_id: str) -> str:
    base = get_settings().workspace_root
    return os.path.join(base, "artifacts", "matrix_script_shot_material", str(task_id), str(shot_id))


def material_handle(task_id: str, shot_id: str, filename: str) -> str:
    return f"{MATERIAL_HANDLE_SCHEME}{task_id}/{shot_id}/{filename}"


def material_preview_url(task_id: str, shot_id: str) -> str:
    return f"/api/matrix-script/{task_id}/shot-material/{shot_id}/file"


def safe_filename(name: str) -> str:
    base = os.path.basename(str(name or "")).strip()
    base = base.replace("\\", "_").replace("/", "_")
    return base[:200] or "material"


def store_shot_material_bytes(
    *,
    task_id: str,
    shot_id: str,
    filename: str,
    data: bytes,
    declared_kind: Optional[str] = None,
    max_bytes: Optional[int] = None,
) -> StoredShotMaterial:
    """Validate + persist uploaded shot material bytes to the local workspace.

    Rejects empty / oversized files and unsupported kinds; a ``declared_kind``
    that disagrees with the file extension is a hard error so the operator label
    can never mislabel an image as a video (or vice versa).
    """
    if not data:
        raise ShotMaterialStorageError("empty_file")
    limit = max_bytes if max_bytes is not None else DEFAULT_MAX_MB * 1024 * 1024
    if len(data) > limit:
        raise ShotMaterialStorageError("file_too_large")
    fname = safe_filename(filename)
    ext = os.path.splitext(fname)[1].lower()
    kind = material_kind_for_ext(ext)
    if kind is None:
        raise ShotMaterialStorageError("unsupported_file_type")
    if declared_kind and declared_kind != kind:
        raise ShotMaterialStorageError("material_kind_mismatch")
    root = _material_root(task_id, shot_id)
    os.makedirs(root, exist_ok=True)
    local_path = os.path.join(root, fname)
    with open(local_path, "wb") as fh:
        fh.write(data)
    return StoredShotMaterial(
        shot_id=str(shot_id),
        material_kind=kind,
        material_name=fname,
        local_path=local_path,
        material_ref=material_handle(task_id, shot_id, fname),
        preview_url=material_preview_url(task_id, shot_id),
    )


def resolve_shot_material_local_path(
    task_id: str, shot_id: str, material_ref: str
) -> Optional[str]:
    """Resolve a stored ``msmaterial://`` handle to its local byte path, or None.

    Returns None for non-stored handles (e.g. PR-A ``asset://`` references) so the
    caller can tell a resolvable upload apart from a bare reference.
    """
    if not material_ref or not str(material_ref).startswith(MATERIAL_HANDLE_SCHEME):
        return None
    root = _material_root(task_id, shot_id)
    if not os.path.isdir(root):
        return None
    fname = safe_filename(str(material_ref).rsplit("/", 1)[-1])
    path = os.path.join(root, fname)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    return None

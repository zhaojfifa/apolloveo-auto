from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from gateway.app import models
from gateway.app.core.workspace import (
    deliver_pack_zip_path,
    pack_zip_path,
    relative_to_workspace,
    workspace_root,
)
from gateway.app.services.status_policy.service import policy_upsert

PUBLISH_PROVIDER_DEFAULT = os.getenv("PUBLISH_PROVIDER", "local")

R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "")
R2_BUCKET = os.getenv("R2_BUCKET", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_boto3():
    import boto3  # noqa: PLC0415

    return boto3


def _r2_client():
    boto3 = _ensure_boto3()
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _r2_put_file(local_path: Path, key: str) -> None:
    if not (R2_ENDPOINT_URL and R2_BUCKET and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY):
        raise RuntimeError("R2 is not configured (missing R2_* envs)")
    client = _r2_client()
    client.upload_file(str(local_path), R2_BUCKET, key)


def _r2_presign_get(key: str, expires_sec: int = 3600) -> str:
    client = _r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET, "Key": key},
        ExpiresIn=expires_sec,
    )


def _local_publish_copy(task_id: str, src_zip: Path) -> Tuple[str, str]:
    dst = workspace_root() / "published" / task_id
    dst.mkdir(parents=True, exist_ok=True)
    out = dst / "capcut_pack.zip"
    out.write_bytes(src_zip.read_bytes())
    publish_key = str(out)
    return publish_key, relative_to_workspace(out)


def publish_task_pack(
    task_id: str,
    db: Session | None = None,
    *,
    task_repo=None,
    provider: Optional[str] = None,
    force: bool = False,
) -> dict[str, str]:
    task = None
    if task_repo is not None:
        task = task_repo.get(task_id)
    if task is None and db is not None:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise RuntimeError(f"Task not found: {task_id}")

    zip_path = pack_zip_path(task_id)
    if not zip_path.exists():
        zip_path = deliver_pack_zip_path(task_id)
    if not zip_path.exists():
        raise RuntimeError(f"Pack zip not found for task {task_id}: {zip_path}")

    chosen = (provider or getattr(task, "publish_provider", None) or PUBLISH_PROVIDER_DEFAULT).lower()
    if (
        getattr(task, "publish_status", None) == "ready"
        and getattr(task, "publish_key", None)
        and not force
        and chosen == (getattr(task, "publish_provider", None) or chosen)
    ):
        return {
            "provider": getattr(task, "publish_provider", None) or chosen,
            "publish_key": getattr(task, "publish_key", None),
            "download_url": getattr(task, "publish_url", None) or "",
            "published_at": getattr(task, "published_at", None) or "",
        }

    published_at = datetime.utcnow().isoformat()
    sha256 = _sha256_file(zip_path)

    if chosen == "r2":
        key = f"published/{task_id}/capcut_pack_{sha256[:12]}.zip"
        _r2_put_file(zip_path, key)
        if R2_PUBLIC_BASE_URL:
            download_url = f"{R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"
        else:
            download_url = ""
        _publish_upsert(task_id, task_repo=task_repo, db=db, updates={
            "publish_provider": "r2",
            "publish_key": key,
            "publish_url": download_url,
            "publish_status": "ready",
            "published_at": published_at,
        })
        return {
            "provider": "r2",
            "publish_key": key,
            "download_url": download_url,
            "published_at": published_at,
        }

    publish_key, rel = _local_publish_copy(task_id, zip_path)
    _publish_upsert(task_id, task_repo=task_repo, db=db, updates={
        "publish_provider": "local",
        "publish_key": publish_key,
        "publish_url": "",
        "publish_status": "ready",
        "published_at": published_at,
    })
    return {
        "provider": "local",
        "publish_key": publish_key,
        "download_url": rel,
        "published_at": published_at,
    }


def _publish_upsert(task_id: str, *, task_repo=None, db=None, updates: dict) -> None:
    """Write publish state through policy_upsert when possible, fallback to repo/db."""
    if task_repo is not None:
        policy_upsert(task_repo, task_id, None, updates, step="publish")
        return
    if db is not None:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task:
            for k, v in updates.items():
                if hasattr(task, k):
                    setattr(task, k, v)
            db.commit()


def resolve_download_url(task: models.Task) -> str:
    if task.publish_provider == "r2" and task.publish_key:
        if task.publish_url:
            return task.publish_url
        return _r2_presign_get(task.publish_key, expires_sec=3600)

    if task.publish_key:
        p = Path(task.publish_key)
        try:
            rel = relative_to_workspace(p)
            return f"/v1/tasks/{task.id}/pack"
        except Exception:
            pass

    if task.pack_path:
        return f"/v1/tasks/{task.id}/pack"
    return ""

"""Artifact-oriented helper functions shared by task routers.

These helpers were previously kept inline in ``tasks.py``. They do not own
business truth; they only normalize path / artifact utility behavior so router
modules stop depending on each other's private helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from gateway.app.core.workspace import (
    Workspace,
    deliver_pack_zip_path,
    relative_to_workspace,
    task_base_dir,
)
from gateway.app.services.artifact_storage import upload_task_artifact
from gateway.app.services.hot_follow_language_profiles import (
    hot_follow_subtitle_filename,
    hot_follow_subtitle_txt_filename,
)


def is_storage_key(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "s3://", "r2://"))


def pack_path_for_list(task: dict, *, task_value) -> Optional[str]:
    task_id = str(task_value(task, "task_id") or task_value(task, "id") or "")
    pack_type = task_value(task, "pack_type")
    pack_key = task_value(task, "pack_key")
    pack_path = task_value(task, "pack_path")
    if pack_type == "capcut_v18" and pack_key:
        return str(pack_key)
    if pack_path:
        pack_path = str(pack_path)
        if pack_path.startswith(("pack/", "published/")) and not is_storage_key(pack_path):
            return pack_path
    pack_file = deliver_pack_zip_path(task_id)
    if pack_file.exists():
        return relative_to_workspace(pack_file)
    return None


def mm_edited_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "mm_edited.txt"


def load_dub_text(task_id: str) -> tuple[str, str]:
    edited_path = mm_edited_path(task_id)
    if edited_path.exists():
        text = edited_path.read_text(encoding="utf-8").strip()
        if text:
            return text, "mm_edited"
    workspace = Workspace(task_id)
    mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
    if mm_txt_path.exists():
        return mm_txt_path.read_text(encoding="utf-8"), "mm_txt"
    return "", "mm_txt"


def upload_target_subtitle_artifacts(
    task: dict,
    task_id: str,
    target_lang: str,
    *,
    workspace_factory=Workspace,
    artifact_uploader=upload_task_artifact,
) -> tuple[str | None, str | None]:
    workspace = workspace_factory(task_id, target_lang=target_lang)
    subtitle_name = hot_follow_subtitle_filename(target_lang)
    subtitle_txt_name = hot_follow_subtitle_txt_filename(target_lang)
    origin_key = (
        artifact_uploader(task, workspace.origin_srt_path, "origin.srt", task_id=task_id)
        if workspace.origin_srt_path.exists()
        else None
    )
    target_key = (
        artifact_uploader(task, workspace.mm_srt_path, subtitle_name, task_id=task_id)
        if workspace.mm_srt_path.exists()
        else None
    )
    target_txt_path = workspace.mm_srt_path.with_suffix(".txt")
    if target_txt_path.exists():
        artifact_uploader(task, target_txt_path, subtitle_txt_name, task_id=task_id)
    return origin_key, target_key

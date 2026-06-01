"""Matrix Script minimal result internal command (PR-11R).

Controlled service entry point for internal callers:

    task / output_dir
      -> validate Matrix Script task
      -> run_matrix_script_task_minimal_result()
      -> MatrixScriptMinimalResultSurfaceView

This module is a guard seam only. It does not implement outline derivation,
FFmpeg rendering, projection, surface conversion, routes, template actions, or
publish logic.

Hard boundary:
- NO public router endpoint, button/action wiring, UI/template change.
- NO artifact_storage / R2 write; output_dir is explicitly caller supplied.
- NO official publish gate, publish URL, publish status, or task repository
  mutation.
- NO Akool live API / adapter usage; NO webhook / polling.
- NO schema / packet / contract change; NO Hot Follow / Digital Anchor change.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Union

from gateway.app.services.matrix_script.minimal_result_orchestrator import (
    run_matrix_script_task_minimal_result,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    MatrixScriptMinimalResultSurfaceView,
)


class MinimalResultCommandError(ValueError):
    """Raised when the internal command request is invalid."""


def _clean(value: Any) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def _is_matrix_script_task(task: Mapping[str, Any]) -> bool:
    """Return True when task identity is Matrix Script scoped."""
    for key in ("kind", "line_id", "category_key", "category", "platform"):
        if _clean(task.get(key)) == "matrix_script":
            return True

    config = task.get("config")
    if isinstance(config, Mapping):
        if _clean(config.get("line_id")) == "matrix_script":
            return True
        entry = config.get("entry")
        if isinstance(entry, Mapping) and _clean(entry.get("line_id")) == "matrix_script":
            return True

    packet = task.get("packet")
    if isinstance(packet, Mapping) and _clean(packet.get("line_id")) == "matrix_script":
        return True

    return False


def _coerce_output_dir(output_dir: Union[str, "os.PathLike[str]", None]) -> str:
    if output_dir is None:
        raise MinimalResultCommandError("output_dir must be explicitly provided")
    try:
        path = os.fspath(output_dir)
    except TypeError as exc:
        raise MinimalResultCommandError("output_dir must be a filesystem path") from exc
    if not isinstance(path, str) or not path.strip():
        raise MinimalResultCommandError("output_dir must be a non-empty path")
    return path


def run_minimal_result_command(
    task: Mapping[str, Any],
    output_dir: Union[str, "os.PathLike[str]", None],
    *,
    requested_by: str = "internal",
    aspect_ratio: str = "9:16",
    target_duration_seconds: float = 20.0,
) -> MatrixScriptMinimalResultSurfaceView:
    """Run the controlled internal Matrix Script minimal-result command.

    The only production call is PR-10R's orchestrator. Exceptions are not
    swallowed: invalid command inputs raise ``MinimalResultCommandError``;
    FFmpeg absence and render failures bubble from the orchestrator.
    """
    if not isinstance(task, Mapping):
        raise MinimalResultCommandError("task must be a mapping")
    if not _is_matrix_script_task(task):
        raise MinimalResultCommandError("task must be a Matrix Script task")
    output_path = _coerce_output_dir(output_dir)
    if not isinstance(requested_by, str) or not requested_by.strip():
        raise MinimalResultCommandError("requested_by must be a non-empty string")

    return run_matrix_script_task_minimal_result(
        task,
        output_path,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
    )


class MatrixScriptMinimalResultCommand:
    """Small class wrapper for internal service injection."""

    def run(
        self,
        task: Mapping[str, Any],
        output_dir: Union[str, "os.PathLike[str]", None],
        *,
        requested_by: str = "internal",
        aspect_ratio: str = "9:16",
        target_duration_seconds: float = 20.0,
    ) -> MatrixScriptMinimalResultSurfaceView:
        return run_minimal_result_command(
            task,
            output_dir,
            requested_by=requested_by,
            aspect_ratio=aspect_ratio,
            target_duration_seconds=target_duration_seconds,
        )

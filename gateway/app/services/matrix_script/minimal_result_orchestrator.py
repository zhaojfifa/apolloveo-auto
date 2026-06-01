"""Matrix Script minimal result orchestrator (PR-10R).

Chains the already-merged minimal-result modules into one internal service
call that takes an existing Matrix Script task and produces the operator
surface view (backed by a REAL local ``final.mp4``):

    task
      → derive_outline_from_task            (PR-5R service)
      → run_matrix_script_minimal_result    (PR-5R service → real final.mp4)
      → minimal_result_summary_to_record    (PR-6R record)
      → minimal_result_record_to_operator_projection  (PR-7R projection)
      → operator_projection_to_surface_view (PR-8R surface)
      → MatrixScriptMinimalResultSurfaceView

This module only *wires* existing modules; it does not reimplement any of their
logic. It is service-internal — NO UI, NO route, NO button/action wiring.

Hard boundary (PR-10R approval):
- NO UI / template / router change; NO button/action wiring.
- NO Delivery Center runtime change; NO official publish gate / publish logic.
- NO ``artifact_storage`` / R2 write (output goes only to the caller-supplied
  ``output_dir``, a test temp dir in CI).
- NO Akool live API / adapter usage; NO webhook / polling.
- NO schema / packet / contract change; NO Hot Follow / Digital Anchor change.
- If FFmpeg is unavailable, the underlying loop raises
  ``FFmpegUnavailableError`` — a fake ``final.mp4`` is never fabricated.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Union

from gateway.app.services.matrix_script.minimal_result_projection import (
    minimal_result_record_to_operator_projection,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    minimal_result_summary_to_record,
)
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultRequest,
    derive_outline_from_task,
    run_matrix_script_minimal_result,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    MatrixScriptMinimalResultSurfaceView,
    operator_projection_to_surface_view,
)


class MinimalResultOrchestratorError(ValueError):
    """Raised on an invalid orchestrator input (not an ffmpeg-absence case)."""


def run_matrix_script_task_minimal_result(
    task: Mapping[str, Any],
    output_dir: Union[str, "os.PathLike[str]"],
    *,
    aspect_ratio: str = "9:16",
    target_duration_seconds: float = 20.0,
) -> MatrixScriptMinimalResultSurfaceView:
    """Run the full task → surface-view chain. Returns the surface view.

    Produces a real local ``final.mp4`` under ``output_dir``. Raises
    ``FFmpegUnavailableError`` (from the loop) when ffmpeg/ffprobe are missing —
    no fake output is produced. Raises ``MinimalResultOrchestratorError`` on a
    non-mapping task.
    """
    if not isinstance(task, Mapping):
        raise MinimalResultOrchestratorError("task must be a mapping")

    # 1. derive outline (explicit chain step; reuses PR-5R logic)
    outline = derive_outline_from_task(task)

    # 2. run the minimal result service (produces the real final.mp4 + summary)
    request = MatrixScriptMinimalResultRequest(
        output_dir=os.fspath(output_dir),
        task=task,
        outline=outline,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
    )
    summary = run_matrix_script_minimal_result(request)

    # 3. summary → record (PR-6R)
    record = minimal_result_summary_to_record(summary)

    # 4. record → operator projection (PR-7R)
    projection = minimal_result_record_to_operator_projection(record)

    # 5. operator projection → surface view (PR-8R)
    return operator_projection_to_surface_view(projection)

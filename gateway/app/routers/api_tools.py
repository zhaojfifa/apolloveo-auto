import logging
logger = logging.getLogger(__name__)

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from gateway.app.services.tools_registry import get_tool, list_tools, redact_tool, redact_tools

router = APIRouter(prefix="/api", tags=["tools"])


def _http500(message: str) -> HTTPException:
    return HTTPException(status_code=500, detail=message)


@router.get("/tools")
def list_tools_api(
    category: str | None = Query(default=None),
    capabilities: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    integration_level: str | None = Query(default=None),
    status_state: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    try:
        tools = list_tools(
            category=category,
            capabilities=capabilities,
            tags=tags,
            integration_level=integration_level,
            status_state=status_state,
            q=q,
        )
        return {"items": redact_tools(tools), "total": len(tools)}
    except Exception as exc:
        # ✅ 1) 打完整栈：Render Logs 能看到根因
        logger.exception("list_tools_api failed; fallback empty list")
        # ✅ 2) 先止血：tools hub 不再 500
        return {"items": [], "total": 0}



@router.get("/tools/{tool_id}")
def get_tool_api(tool_id: str):
    try:
        tool = get_tool(tool_id)
    except Exception as exc:
        logger.exception("get_tool_api failed tool_id=%s", tool_id)
        raise _http500("internal error") from exc

    if not tool:
        raise HTTPException(status_code=404, detail="tool not found")
    return redact_tool(tool)


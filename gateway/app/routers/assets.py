"""Operator-visible Asset Supply / B-roll surface
(Operator Capability Recovery, PR-2).

Mounts the minimum operator surface for browsing the asset library,
applying closed-facet filters, taking opaque references for cross-task
use, submitting promote intents, and reading promote-closure status.

Distinct from Task Area (`/tasks*`) and Tool Backstage (`/admin/*`,
`/tools/*`). The surface is intentionally narrow: no upload, no admin
review UI, no provider/model controls. All shapes trace to:

- `docs/contracts/asset_library_object_contract_v1.md`
- `docs/contracts/promote_request_contract_v1.md`
- `docs/contracts/promote_feedback_closure_contract_v1.md`
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from gateway.app.services.asset import (
    PromoteRequestRejected,
    get_asset,
    get_closure,
    list_assets,
    list_closures,
    list_known_kinds,
    list_known_lines,
    list_known_quality_buckets,
    reference_asset,
    submit_promote_request,
    withdraw_request,
)
from gateway.app.web.templates import get_templates

# Operator-visible page surface. Mounted independently of `/tasks` so
# Task Area and Asset Supply remain distinct surfaces per
# `broll_asset_supply_freeze_v1.md` §0 "Boundary".
page_router = APIRouter(prefix="/assets", tags=["assets-page"])

# JSON capability surface (mounted under `/api/assets` to keep operator
# JSON consumers separate from page rendering).
api_router = APIRouter(prefix="/api/assets", tags=["assets-api"])


def _filter_kwargs(
    line: Optional[str],
    kind: Optional[str],
    quality_filter: Optional[str],
) -> dict[str, Any]:
    return {
        "line": line or None,
        "kind": kind or None,
        "quality_filter": quality_filter or None,
    }


@page_router.get("", response_class=HTMLResponse)
def assets_page(
    request: Request,
    line: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    quality_filter: Optional[str] = Query(default=None, alias="quality"),
) -> HTMLResponse:
    """Operator-visible Asset Supply page.

    Renders the contract-shaped catalog with closed-facet filters and
    per-row promote affordance. The page is read-driven; the promote
    submit and closure read endpoints live under `/api/assets/...`.
    """
    try:
        assets = list_assets(**_filter_kwargs(line, kind, quality_filter))
    except ValueError as exc:
        # Closed-enum violation on the query string — surface as 400 so
        # the operator sees the rejection reason, not a 500.
        raise HTTPException(status_code=400, detail=str(exc))
    closures = list_closures()
    templates = get_templates()
    return templates.TemplateResponse(
        "assets.html",
        {
            "request": request,
            "assets": assets,
            "closures": closures,
            "filters": {
                "line": line,
                "kind": kind,
                "quality_filter": quality_filter,
            },
            "filter_options": {
                "lines": list_known_lines(),
                "kinds": list_known_kinds(),
                "quality_buckets": list_known_quality_buckets(),
            },
        },
    )


@api_router.get("")
def list_assets_api(
    line: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    quality_filter: Optional[str] = Query(default=None, alias="quality"),
) -> JSONResponse:
    try:
        assets = list_assets(**_filter_kwargs(line, kind, quality_filter))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({"assets": assets, "count": len(assets)})


@api_router.get("/{asset_id}")
def get_asset_api(asset_id: str) -> JSONResponse:
    asset = get_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return JSONResponse(asset)


@api_router.get("/{asset_id}/reference")
def reference_asset_api(asset_id: str) -> JSONResponse:
    """Return the opaque reference handle for cross-task referencing.

    Per `broll_asset_supply_freeze_v1.md` §0, packets reference assets
    by `asset_id` only — never by metadata embed. This endpoint
    formalizes the opaque handle (`asset://<asset_id>`) so a Workbench /
    Task Area caller cannot accidentally widen the reference shape.
    """
    handle = reference_asset(asset_id)
    if handle is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return JSONResponse(handle)


@api_router.post("/promote")
async def submit_promote_api(request: Request) -> JSONResponse:
    """Submit a promote intent against the closed request schema.

    Returns `{"request_id": str, "request_state": "requested"}` only;
    asset_id is decided asynchronously per the request contract.
    """
    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001 — JSON parse boundary
        raise HTTPException(status_code=400, detail=f"invalid_json:{exc}")
    try:
        result = submit_promote_request(payload)
    except PromoteRequestRejected as exc:
        return JSONResponse(
            {"error_code": exc.error_code, "message": str(exc)},
            status_code=400,
        )
    return JSONResponse(result, status_code=201)


@api_router.get("/promote/{request_id}")
def get_promote_closure_api(request_id: str) -> JSONResponse:
    closure = get_closure(request_id)
    if closure is None:
        raise HTTPException(status_code=404, detail="closure_not_found")
    return JSONResponse(closure)


@api_router.post("/promote/{request_id}/withdraw")
async def withdraw_promote_api(request_id: str, request: Request) -> JSONResponse:
    """Operator-initiated withdrawal before terminal state."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    actor_ref = (body.get("actor_ref") if isinstance(body, dict) else None) or "operator:unknown"
    try:
        closure = withdraw_request(request_id, actor_ref=str(actor_ref))
    except PromoteRequestRejected as exc:
        status = 404 if exc.error_code == "closure_not_found" else 409
        return JSONResponse(
            {"error_code": exc.error_code, "message": str(exc)},
            status_code=status,
        )
    return JSONResponse(closure)


__all__ = ["api_router", "page_router"]

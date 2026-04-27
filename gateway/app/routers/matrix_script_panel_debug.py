from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from gateway.app.services.matrix_script.workbench_variation_surface import (
    project_workbench_variation_surface,
)

router = APIRouter(prefix="/debug/panels/matrix-script", tags=["debug-panels"])

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_HTML = REPO_ROOT / "gateway" / "app" / "static" / "panel_html.html"
SAMPLE_PACKET = (
    REPO_ROOT
    / "schemas"
    / "packets"
    / "matrix_script"
    / "sample"
    / "matrix_script_packet_v1.sample.json"
)


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def matrix_script_panel() -> HTMLResponse:
    html = STATIC_HTML.read_text(encoding="utf-8")
    html = html.replace('href="panel_css.css"', 'href="/static/panel_css.css"')
    html = html.replace('src="panel_js.js"', 'src="/static/panel_js.js"')
    return HTMLResponse(html)


@router.get("/data")
def matrix_script_panel_data() -> Dict[str, Any]:
    packet = json.loads(SAMPLE_PACKET.read_text(encoding="utf-8"))
    return {
        "source": "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json",
        "packet_instance": packet,
        "panel_data": project_workbench_variation_surface(packet),
    }

from __future__ import annotations

from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette.templating import Jinja2Templates

from gateway.app.web.template_helpers import get_template_globals

_templates: Jinja2Templates | None = None


def _template_context(request: Request) -> dict[str, object]:
    """Compute template globals per-request to avoid shared state drifting."""
    return get_template_globals(request)


def get_templates() -> Jinja2Templates:
    """
    Lazy accessor for templates to avoid import-time initialization.
    """
    global _templates
    if _templates is None:
        templates = Jinja2Templates(directory="gateway/app/templates")
        # Use a context processor so globals refresh per request (env globals are shared
        # across requests and can become stale if settings or language preferences
        # change at runtime).
        templates.context_processors.append(_template_context)
        _templates = templates
    return _templates


def render_template(*, request: Request, name: str, ctx: Optional[Dict[str, Any]] = None):
    """
    Render a template with per-request i18n globals injected.
    """
    data: Dict[str, Any] = {"request": request}
    if ctx:
        data.update(ctx)
    data.update(get_template_globals(request))
    return get_templates().TemplateResponse(name, data)

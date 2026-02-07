"""Compatibility entrypoint.

This file must NOT assemble FastAPI.
Single composition root: gateway/app/main.py
"""

from gateway.app.main import app  # noqa: F401

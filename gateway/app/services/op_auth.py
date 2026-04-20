"""Shared operator key validation helpers."""

from __future__ import annotations

import hmac

from gateway.app.core.constants import OP_HEADER_KEY
from gateway.app.services.task_view_helpers import _get_op_access_key


def op_key_valid_value(op_key: str | None) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    if not op_key:
        return False
    return hmac.compare_digest(op_key, secret)


def op_key_valid_request(request) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    header_val = (request.headers.get(OP_HEADER_KEY) or "").strip()
    return hmac.compare_digest(header_val, secret)

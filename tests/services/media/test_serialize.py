"""Unit tests for M-04 serialize helper.

Verifies `to_jsonable_dict` behavior is preserved verbatim from the donor
(SwiftCraft `backend/app/utils/serialize.py`, donor commit pin 62b6da0).
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from gateway.app.services.media.serialize import to_jsonable_dict


def test_dict_with_model_dump_takes_precedence():
    class HasModelDump:
        def model_dump(self):
            return {"via": "model_dump"}

        def dict(self):  # noqa: A003 - mirror pydantic v1 surface
            return {"via": "dict"}

    assert to_jsonable_dict(HasModelDump()) == {"via": "model_dump"}


def test_dict_method_used_when_no_model_dump():
    class HasDict:
        def dict(self):  # noqa: A003
            return {"via": "dict"}

    assert to_jsonable_dict(HasDict()) == {"via": "dict"}


def test_dataclass_via_asdict():
    @dataclass
    class D:
        a: int
        b: str

    assert to_jsonable_dict(D(a=1, b="x")) == {"a": 1, "b": "x"}


def test_plain_object_via_dunder_dict():
    class Plain:
        def __init__(self):
            self.x = 1
            self.y = "y"

    assert to_jsonable_dict(Plain()) == {"x": 1, "y": "y"}


def test_unsupported_type_raises_type_error():
    with pytest.raises(TypeError):
        to_jsonable_dict(42)

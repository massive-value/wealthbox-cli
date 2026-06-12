"""Meta-test: every *UpdateInput model must reject an empty payload.

This test discovers all classes whose name ends with ``UpdateInput`` by
walking the ``wealthbox_tools.models`` package submodules, then asserts that
constructing each one with no arguments raises ``pydantic.ValidationError``.

Adding a new ``*UpdateInput`` model that does NOT inherit
``RequireAnyFieldModel`` (or an equivalent ``@model_validator``) will cause
this test to fail immediately, surfacing the omission before it reaches
production.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Type

import pytest
from pydantic import BaseModel, ValidationError

import wealthbox_tools.models as _models_pkg


def _discover_update_inputs() -> list[tuple[str, Type[BaseModel]]]:
    """Walk every submodule of ``wealthbox_tools.models`` and collect all
    classes whose name ends with ``UpdateInput`` and whose base is
    ``pydantic.BaseModel`` (directly or transitively).
    """
    found: dict[str, Type[BaseModel]] = {}

    pkg_path = _models_pkg.__path__  # type: ignore[attr-defined]
    pkg_name = _models_pkg.__name__

    for _finder, modname, _ispkg in pkgutil.iter_modules(pkg_path):
        module = importlib.import_module(f"{pkg_name}.{modname}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                name.endswith("UpdateInput")
                and issubclass(obj, BaseModel)
                and obj.__module__ == module.__name__  # defined here, not re-imported
            ):
                found[name] = obj

    return sorted(found.items())  # stable alphabetical order for parametrize IDs


_UPDATE_INPUTS = _discover_update_inputs()


@pytest.mark.parametrize("model_name,model_cls", _UPDATE_INPUTS, ids=[n for n, _ in _UPDATE_INPUTS])
def test_update_input_rejects_empty_payload(model_name: str, model_cls: Type[BaseModel]) -> None:
    """Constructing *UpdateInput with no arguments must raise ValidationError."""
    with pytest.raises(ValidationError, match="(?i)(at least one field|field required)"):
        model_cls()

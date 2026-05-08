"""Firm-archive packaging.

Public surface:
- ``pack(firm_dir)`` — zip a firm directory into a portable byte blob.
- ``unpack(source)`` — read a firm-archive zip into an :class:`ImportPlan`.
- ``apply(plan, firm_dir, mode)`` — write a plan onto a firm directory.
- ``ApplyMode`` — overwrite / merge / abort-on-conflict (only overwrite is
  implemented in the current slice).
- ``ArchiveError`` — raised for malformed archives or unsupported modes.
"""
from __future__ import annotations

from .archive import (
    ApplyMode,
    ApplyResult,
    ArchiveError,
    ImportPlan,
    apply,
    pack,
    unpack,
)

__all__ = [
    "ApplyMode",
    "ApplyResult",
    "ArchiveError",
    "ImportPlan",
    "apply",
    "pack",
    "unpack",
]

"""Firm-archive packaging.

Public surface:
- ``pack(firm_dir)`` — zip a firm directory into a portable byte blob.
"""
from __future__ import annotations

from .archive import pack

__all__ = ["pack"]

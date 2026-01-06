"""Queryregistry provider helpers."""

from __future__ import annotations

from . import mssql

PROVIDERS = {
  "mssql": mssql,
}

__all__ = ["PROVIDERS", "mssql"]

"""Queryregistry provider helpers."""

from __future__ import annotations

from . import mssql, mysql, postgres

PROVIDERS = {
  "mssql": mssql,
  "mysql": mysql,
  "postgres": postgres,
}

__all__ = ["PROVIDERS", "mssql", "mysql", "postgres"]

"""MSSQL implementations for public users query registry services."""

from __future__ import annotations

from server.queryregistry.types import CheckStatusPayload

__all__ = ["check_status"]


async def check_status() -> CheckStatusPayload:
  return {"status": "ok", "provider": "mssql"}

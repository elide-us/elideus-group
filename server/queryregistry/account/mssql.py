"""MSSQL implementations for account query registry services."""

from __future__ import annotations

from .models import AccountCheckStatusPayload

__all__ = ["check_status"]


async def check_status() -> AccountCheckStatusPayload:
  return {"status": "ok", "provider": "mssql"}

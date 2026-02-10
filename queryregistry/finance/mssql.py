"""MSSQL implementations for finance query registry services."""

from __future__ import annotations

from .models import FinanceCheckStatusPayload

__all__ = ["check_status"]


async def check_status() -> FinanceCheckStatusPayload:
  return {"status": "ok", "provider": "mssql"}

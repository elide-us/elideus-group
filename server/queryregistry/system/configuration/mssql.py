"""MSSQL implementations for system configuration query registry services."""

from __future__ import annotations

from ..models import SystemCheckStatusPayload

__all__ = ["check_status"]


async def check_status() -> SystemCheckStatusPayload:
  return {"status": "ok", "provider": "mssql"}

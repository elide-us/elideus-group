"""System configuration query handler package."""

from __future__ import annotations

from typing import Protocol

from server.queryregistry.models import DBRequest, DBResponse

from .services import system_check_status_v1

__all__ = ["DISPATCHERS"]

class _SubdomainDispatcher(Protocol):
  async def __call__(self, request: DBRequest, *, provider: str) -> DBResponse: ...


DISPATCHERS: dict[tuple[str, str], _SubdomainDispatcher] = {
  ("check_status", "1"): system_check_status_v1,
}

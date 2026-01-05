"""Configuration subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .services import system_check_status_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_configuration_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("check_status", "1"): system_check_status_v1,
}


async def handle_configuration_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if len(path) < 2:
    raise HTTPException(status_code=404, detail="Unknown system configuration operation")
  key = tuple(path[:2])
  handler = DISPATCHERS.get(key)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown system configuration operation")
  return await handler(request, provider=provider)

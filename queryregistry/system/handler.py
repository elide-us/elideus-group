"""System domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from . import HANDLERS

__all__ = ["handle_system_request"]


async def handle_system_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown system registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown system registry operation")
  return await handler(path[1:], request, provider=provider)

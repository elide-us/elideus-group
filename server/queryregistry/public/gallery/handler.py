"""Public gallery query handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from server.queryregistry.models import DBRequest, DBResponse

from . import DISPATCHERS

__all__ = ["handle_gallery_request"]


async def handle_gallery_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if len(path) < 2:
    raise HTTPException(status_code=404, detail="Unknown public gallery operation")
  key = tuple(path[:2])
  handler = DISPATCHERS.get(key)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown public gallery operation")
  return await handler(request, provider=provider)

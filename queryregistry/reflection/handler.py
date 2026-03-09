"""Reflection domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .data.handler import handle_data_request
from .schema.handler import handle_schema_request

__all__ = ["handle_reflection_request"]

HANDLERS = {
  "schema": handle_schema_request,
  "data": handle_data_request,
}


async def handle_reflection_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown reflection registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown reflection registry operation")
  return await handler(path[1:], request, provider=provider)

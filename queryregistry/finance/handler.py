"""Finance domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .credits.handler import handle_credits_request
from .status.handler import handle_status_request

__all__ = ["handle_finance_request"]

HANDLERS = {
  "credits": handle_credits_request,
  "status": handle_status_request,
}


async def handle_finance_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown finance registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown finance registry operation")
  return await handler(path[1:], request, provider=provider)

"""Handlers for the public query namespace."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from server.queryregistry.models import DBRequest, DBResponse

from . import HANDLERS


async def handle_public_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  """Dispatch a public query subdomain request."""

  if not path:
    raise HTTPException(status_code=404, detail="Unknown query subdomain")
  subdomain, *remainder = path
  handler = HANDLERS.get(subdomain)
  if not handler:
    raise HTTPException(status_code=404, detail="Unknown query subdomain")
  return await handler(tuple(remainder), request, provider=provider)

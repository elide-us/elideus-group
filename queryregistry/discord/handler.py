"""Discord domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .channels.handler import handle_channels_request
from .guilds.handler import handle_guilds_request

__all__ = ["handle_discord_request"]

HANDLERS = {
  "guilds": handle_guilds_request,
  "channels": handle_channels_request,
}


async def handle_discord_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown discord registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown discord registry operation")
  return await handler(path[1:], request, provider=provider)

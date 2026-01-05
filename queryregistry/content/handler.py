"""Content domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .assets.handler import handle_assets_request
from .cache.handler import handle_cache_request
from .galleries.handler import handle_galleries_request
from .moderation.handler import handle_moderation_request
from .visibility.handler import handle_visibility_request

__all__ = ["handle_content_request"]

HANDLERS = {
  "assets": handle_assets_request,
  "cache": handle_cache_request,
  "galleries": handle_galleries_request,
  "moderation": handle_moderation_request,
  "visibility": handle_visibility_request,
}


async def handle_content_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown content registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown content registry operation")
  return await handler(path[1:], request, provider=provider)

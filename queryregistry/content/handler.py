"""Content domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .cache.handler import handle_cache_request
from .indexing.handler import handle_indexing_request
from .pages.handler import handle_pages_request
from .posts.handler import handle_posts_request
from .wiki.handler import handle_wiki_request

__all__ = ["handle_content_request"]

HANDLERS = {
  "cache": handle_cache_request,
  "indexing": handle_indexing_request,
  "pages": handle_pages_request,
  "posts": handle_posts_request,
  "wiki": handle_wiki_request,
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

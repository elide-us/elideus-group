"""Content wiki handler implementations (stub)."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse
from queryregistry.stubs import build_stub_dispatchers

__all__ = ["handle_wiki_request"]

DISPATCHERS = build_stub_dispatchers("content.wiki")


async def handle_wiki_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown content wiki operation",
  )

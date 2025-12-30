"""Shared dispatch helpers for query registry subdomains."""

from __future__ import annotations

from typing import Awaitable, Callable, Mapping, Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

SubdomainDispatcher = Callable[[DBRequest], Awaitable[DBResponse]]


def _normalize_detail(detail: str) -> str:
  return detail or "Unknown registry operation"


async def dispatch_subdomain_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
  dispatchers: Mapping[tuple[str, str], SubdomainDispatcher],
  detail: str,
) -> DBResponse:
  if len(path) < 2:
    raise HTTPException(status_code=404, detail=_normalize_detail(detail))
  key = tuple(path[:2])
  handler = dispatchers.get(key)
  if handler is None:
    raise HTTPException(status_code=404, detail=_normalize_detail(detail))
  return await handler(request, provider=provider)

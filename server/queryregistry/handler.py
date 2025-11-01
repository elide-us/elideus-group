"""Dispatch helpers for query registry operations."""

from __future__ import annotations

from typing import Awaitable, Callable, Sequence

from server.queryregistry.models import DBRequest, DBResponse

from . import HANDLERS
from .helpers import parse_query_request

DomainHandler = Callable[[Sequence[str], DBRequest, str], Awaitable[DBResponse]]


async def dispatch_query_request(
  db_request: DBRequest,
  *,
  provider: str = "mssql",
) -> DBResponse:
  domain, segments = parse_query_request(db_request)
  handler = HANDLERS.get(domain)
  if handler is None:
    raise KeyError(f"Unknown query registry domain: {domain}")
  return await handler(tuple(segments), db_request, provider=provider)

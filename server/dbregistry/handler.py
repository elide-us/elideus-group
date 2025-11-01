"""Dispatch helpers for database registry operations."""

from __future__ import annotations

from typing import Awaitable, Callable, Sequence

from server.registry.models import DBRequest, DBResponse

from . import HANDLERS
from .helpers import parse_db_request

DomainHandler = Callable[[Sequence[str], DBRequest, str], Awaitable[DBResponse]]


async def dispatch_db_request(
  db_request: DBRequest,
  *,
  provider: str = "mssql",
) -> DBResponse:
  domain, segments = parse_db_request(db_request)
  handler = HANDLERS.get(domain)
  if handler is None:
    raise KeyError(f"Unknown database registry domain: {domain}")
  return await handler(tuple(segments), db_request, provider=provider)

"""Dispatch helpers for query registry operations."""

from __future__ import annotations

from typing import Awaitable, Callable, Sequence

from queryregistry.models import DBRequest, DBResponse

from .discord.handler import handle_discord_request
from .identity.handler import handle_identity_request
from .system.handler import handle_system_request
from .helpers import parse_query_request

DomainHandler = Callable[[Sequence[str], DBRequest, str], Awaitable[DBResponse]]
HANDLERS: dict[str, DomainHandler] = {
  "discord": handle_discord_request,
  "identity": handle_identity_request,
  "system": handle_system_request,
}


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

"""Discord guilds handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_guild_v1, list_guilds_v1, update_credits_v1, upsert_guild_v1

__all__ = ["handle_guilds_request"]

DISPATCHERS = {
  ("upsert", "1"): upsert_guild_v1,
  ("get", "1"): get_guild_v1,
  ("list", "1"): list_guilds_v1,
  ("update_credits", "1"): update_credits_v1,
}


async def handle_guilds_request(
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
    detail="Unknown discord guilds operation",
  )

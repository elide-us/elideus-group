"""Discord channels handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import bump_activity_v1, get_channel_v1, list_by_guild_v1, upsert_channel_v1

__all__ = ["handle_channels_request"]

DISPATCHERS = {
  ("upsert", "1"): upsert_channel_v1,
  ("get", "1"): get_channel_v1,
  ("list_by_guild", "1"): list_by_guild_v1,
  ("bump_activity", "1"): bump_activity_v1,
}


async def handle_channels_request(
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
    detail="Unknown discord channels operation",
  )

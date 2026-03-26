"""Identity users handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import account_exists_v1, read_discord_security_v1, read_users_v1

__all__ = ["handle_users_request"]

DISPATCHERS = {
  ("read", "1"): read_users_v1,
  ("exists", "1"): account_exists_v1,
  ("read_by_discord", "1"): read_discord_security_v1,
}


async def handle_users_request(
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
    detail="Unknown identity users operation",
  )

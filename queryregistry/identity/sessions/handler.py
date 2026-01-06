"""Identity sessions handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import read_sessions_v1

__all__ = ["handle_sessions_request"]

DISPATCHERS = {
  ("read", "1"): read_sessions_v1,
}


async def handle_sessions_request(
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
    detail="Unknown identity sessions operation",
  )

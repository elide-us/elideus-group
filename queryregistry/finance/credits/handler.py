"""Finance credits subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_v1, set_v1

__all__ = ["handle_credits_request"]

DISPATCHERS = {
  ("get", "1"): get_v1,
  ("set", "1"): set_v1,
}


async def handle_credits_request(
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
    detail="Unknown finance credits operation",
  )

"""Identity enablements handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_v1, upsert_v1

__all__ = ["handle_enablements_request"]

DISPATCHERS = {
  ("get", "1"): get_v1,
  ("upsert", "1"): upsert_v1,
}


async def handle_enablements_request(
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
    detail="Unknown identity enablements operation",
  )

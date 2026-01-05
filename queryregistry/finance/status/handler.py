"""Finance status subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from ..services import finance_check_status_v1

__all__ = ["handle_status_request"]

DISPATCHERS = {
  ("check_status", "1"): finance_check_status_v1,
}


async def handle_status_request(
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
    detail="Unknown finance status operation",
  )

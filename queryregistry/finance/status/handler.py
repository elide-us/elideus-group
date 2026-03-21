"""Finance status code subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_status_code_v1, list_status_codes_v1

__all__ = ["handle_status_request"]

DISPATCHERS = {
  ("list", "1"): list_status_codes_v1,
  ("get_by_domain_code", "1"): get_status_code_v1,
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

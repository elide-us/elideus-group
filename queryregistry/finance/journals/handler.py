"""Finance journals subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import create_v1, get_by_posting_key_v1, get_v1, list_v1, update_status_v1

__all__ = ["handle_journals_request"]

DISPATCHERS = {
  ("list", "1"): list_v1,
  ("get", "1"): get_v1,
  ("create", "1"): create_v1,
  ("update_status", "1"): update_status_v1,
  ("get_by_posting_key", "1"): get_by_posting_key_v1,
}


async def handle_journals_request(
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
    detail="Unknown finance journals operation",
  )

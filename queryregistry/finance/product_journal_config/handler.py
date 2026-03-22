"""Finance product journal config subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import activate_v1, approve_v1, close_v1, get_active_v1, get_v1, list_v1, upsert_v1

__all__ = ["handle_product_journal_config_request"]

DISPATCHERS = {
  ("list", "1"): list_v1,
  ("get", "1"): get_v1,
  ("get_active", "1"): get_active_v1,
  ("upsert", "1"): upsert_v1,
  ("approve", "1"): approve_v1,
  ("activate", "1"): activate_v1,
  ("close", "1"): close_v1,
}


async def handle_product_journal_config_request(
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
    detail="Unknown finance product_journal_config operation",
  )

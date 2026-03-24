"""Finance staging account map subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  delete_account_map_v1,
  get_account_map_v1,
  list_account_map_v1,
  resolve_account_v1,
  upsert_account_map_v1,
)

__all__ = ["handle_staging_account_map_request"]

DISPATCHERS = {
  ("list_account_map", "1"): list_account_map_v1,
  ("get_account_map", "1"): get_account_map_v1,
  ("upsert_account_map", "1"): upsert_account_map_v1,
  ("delete_account_map", "1"): delete_account_map_v1,
  ("resolve_account", "1"): resolve_account_v1,
}


async def handle_staging_account_map_request(
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
    detail="Unknown finance staging_account_map operation",
  )

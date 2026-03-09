"""Reflection data handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import apply_batch_v1, dump_table_v1, get_version_v1, rebuild_indexes_v1, update_version_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_data_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_version", "1"): get_version_v1,
  ("update_version", "1"): update_version_v1,
  ("dump_table", "1"): dump_table_v1,
  ("rebuild_indexes", "1"): rebuild_indexes_v1,
  ("apply_batch", "1"): apply_batch_v1,
}


async def handle_data_request(
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
    detail="Unknown reflection data operation",
  )

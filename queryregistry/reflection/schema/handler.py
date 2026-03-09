"""Reflection schema handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  get_full_schema_v1,
  list_columns_v1,
  list_foreign_keys_v1,
  list_indexes_v1,
  list_tables_v1,
  list_views_v1,
)
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_schema_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list_tables", "1"): list_tables_v1,
  ("list_columns", "1"): list_columns_v1,
  ("list_indexes", "1"): list_indexes_v1,
  ("list_foreign_keys", "1"): list_foreign_keys_v1,
  ("list_views", "1"): list_views_v1,
  ("get_full_schema", "1"): get_full_schema_v1,
}


async def handle_schema_request(
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
    detail="Unknown reflection schema operation",
  )

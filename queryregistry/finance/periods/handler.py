"""Finance periods subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  close_v1,
  delete_v1,
  generate_calendar_v1,
  get_v1,
  list_by_year_v1,
  list_close_blockers_v1,
  list_v1,
  lock_v1,
  reopen_v1,
  unlock_v1,
  upsert_v1,
)

__all__ = ["handle_periods_request"]

DISPATCHERS = {
  ("list", "1"): list_v1,
  ("list_by_year", "1"): list_by_year_v1,
  ("get", "1"): get_v1,
  ("close", "1"): close_v1,
  ("reopen", "1"): reopen_v1,
  ("lock", "1"): lock_v1,
  ("unlock", "1"): unlock_v1,
  ("list_close_blockers", "1"): list_close_blockers_v1,
  ("upsert", "1"): upsert_v1,
  ("delete", "1"): delete_v1,
  ("generate_calendar", "1"): generate_calendar_v1,
}


async def handle_periods_request(
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
    detail="Unknown finance periods operation",
  )

"""Finance numbers subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import close_sequence_v1, delete_v1, get_by_prefix_account_v1, get_v1, list_v1, next_number_v1, upsert_v1

__all__ = ["handle_numbers_request"]

DISPATCHERS = {
  ("list", "1"): list_v1,
  ("get", "1"): get_v1,
  ("get_by_prefix_account", "1"): get_by_prefix_account_v1,
  ("upsert", "1"): upsert_v1,
  ("delete", "1"): delete_v1,
  ("close_sequence", "1"): close_sequence_v1,
  ("next_number", "1"): next_number_v1,
}


async def handle_numbers_request(
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
    detail="Unknown finance numbers operation",
  )

"""Finance ledgers subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_v1,
  delete_v1,
  get_by_name_v1,
  get_v1,
  journal_reference_count_v1,
  list_v1,
  update_v1,
)

__all__ = ["handle_ledgers_request"]

DISPATCHERS = {
  ("create", "1"): create_v1,
  ("delete", "1"): delete_v1,
  ("get", "1"): get_v1,
  ("get_by_name", "1"): get_by_name_v1,
  ("journal_reference_count", "1"): journal_reference_count_v1,
  ("list", "1"): list_v1,
  ("update", "1"): update_v1,
}


async def handle_ledgers_request(
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
    detail="Unknown finance ledgers operation",
  )

"""Finance staging subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_import_v1,
  insert_cost_detail_batch_v1,
  list_cost_details_by_import_v1,
  list_imports_v1,
  update_import_status_v1,
)

__all__ = ["handle_staging_request"]

DISPATCHERS = {
  ("create_import", "1"): create_import_v1,
  ("update_import_status", "1"): update_import_status_v1,
  ("insert_cost_detail_batch", "1"): insert_cost_detail_batch_v1,
  ("list_imports", "1"): list_imports_v1,
  ("list_cost_details_by_import", "1"): list_cost_details_by_import_v1,
}


async def handle_staging_request(
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
    detail="Unknown finance staging operation",
  )

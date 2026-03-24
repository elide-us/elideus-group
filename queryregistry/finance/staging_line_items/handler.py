from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  aggregate_line_items_v1,
  delete_line_items_by_import_v1,
  insert_line_items_batch_v1,
  list_line_items_by_import_v1,
)

DISPATCHERS = {
  ("insert_line_items_batch", "1"): insert_line_items_batch_v1,
  ("list_line_items_by_import", "1"): list_line_items_by_import_v1,
  ("aggregate_line_items", "1"): aggregate_line_items_v1,
  ("delete_line_items_by_import", "1"): delete_line_items_by_import_v1,
}


async def handle_staging_line_items_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown finance staging_line_items operation",
  )

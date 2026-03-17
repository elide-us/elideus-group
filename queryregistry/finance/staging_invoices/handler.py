from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  delete_invoices_by_import_v1,
  get_invoice_by_name_v1,
  insert_invoice_batch_v1,
  list_invoices_by_import_v1,
)

DISPATCHERS = {
  ("insert_invoice_batch", "1"): insert_invoice_batch_v1,
  ("list_invoices_by_import", "1"): list_invoices_by_import_v1,
  ("get_invoice_by_name", "1"): get_invoice_by_name_v1,
  ("delete_invoices_by_import", "1"): delete_invoices_by_import_v1,
}


async def handle_staging_invoices_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown finance staging_invoices operation",
  )

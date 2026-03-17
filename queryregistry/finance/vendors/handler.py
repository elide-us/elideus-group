from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import delete_vendor_v1, get_vendor_by_name_v1, get_vendor_v1, list_vendors_v1, upsert_vendor_v1

DISPATCHERS = {
  ("list_vendors", "1"): list_vendors_v1,
  ("get_vendor", "1"): get_vendor_v1,
  ("get_vendor_by_name", "1"): get_vendor_by_name_v1,
  ("upsert_vendor", "1"): upsert_vendor_v1,
  ("delete_vendor", "1"): delete_vendor_v1,
}


async def handle_vendors_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown finance vendors operation",
  )

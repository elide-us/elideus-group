"""RPC dispatch model_fields handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import list_model_fields_v1, get_model_fields_v1, list_by_model_model_fields_v1, upsert_model_fields_v1, delete_model_fields_v1
from ..dispatch import SubdomainDispatcher

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_model_fields_v1,
  ("get", "1"): get_model_fields_v1,
  ("list_by_model", "1"): list_by_model_model_fields_v1,
  ("upsert", "1"): upsert_model_fields_v1,
  ("delete", "1"): delete_model_fields_v1,
}


async def handle_model_fields_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  return await dispatch_subdomain_request(path, request, provider=provider, dispatchers=DISPATCHERS, detail="Unknown rpcdispatch model_fields operation")

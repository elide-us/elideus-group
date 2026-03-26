"""RPC dispatch domains handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import list_domains_v1, get_domains_v1, get_by_name_domains_v1, upsert_domains_v1, delete_domains_v1
from ..dispatch import SubdomainDispatcher

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_domains_v1,
  ("get", "1"): get_domains_v1,
  ("get_by_name", "1"): get_by_name_domains_v1,
  ("upsert", "1"): upsert_domains_v1,
  ("delete", "1"): delete_domains_v1,
}


async def handle_domains_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  return await dispatch_subdomain_request(path, request, provider=provider, dispatchers=DISPATCHERS, detail="Unknown rpcdispatch domains operation")

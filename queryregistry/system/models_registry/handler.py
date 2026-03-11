"""System models handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import delete_v1, get_by_name_v1, list_v1, upsert_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_models_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_v1,
  ("get_by_name", "1"): get_by_name_v1,
  ("upsert", "1"): upsert_v1,
  ("delete", "1"): delete_v1,
}


async def handle_models_request(
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
    detail="Unknown system models operation",
  )

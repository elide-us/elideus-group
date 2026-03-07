"""System routes handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import delete_route_v1, get_routes_v1, upsert_route_v1

__all__ = ["handle_routes_request"]

DISPATCHERS = {
  ("get_routes", "1"): get_routes_v1,
  ("upsert_route", "1"): upsert_route_v1,
  ("delete_route", "1"): delete_route_v1,
}


async def handle_routes_request(
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
    detail="Unknown system routes operation",
  )

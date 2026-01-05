"""System links handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_home_links_v1, get_navbar_routes_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_links_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_home_links", "1"): get_home_links_v1,
  ("get_navbar_routes", "1"): get_navbar_routes_v1,
}


async def handle_links_request(
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
    detail="Unknown system links operation",
  )

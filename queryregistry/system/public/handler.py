"""System public handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  delete_route_v1,
  get_cms_tree_for_path_v1,
  get_config_value_v1,
  get_home_links_v1,
  get_navbar_routes_v1,
  get_routes_v1,
  list_frontend_pages_v1,
  upsert_route_v1,
  get_cms_shell_tree_v1,
  get_page_data_bindings_v1,
)
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_public_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_cms_tree_for_path", "1"): get_cms_tree_for_path_v1,
  ("get_config_value", "1"): get_config_value_v1,
  ("get_home_links", "1"): get_home_links_v1,
  ("get_navbar_routes", "1"): get_navbar_routes_v1,
  ("get_routes", "1"): get_routes_v1,
  ("list_frontend_pages", "1"): list_frontend_pages_v1,
  ("upsert_route", "1"): upsert_route_v1,
  ("delete_route", "1"): delete_route_v1,
  ("get_cms_shell_tree", "1"): get_cms_shell_tree_v1,
  ("get_page_data_bindings", "1"): get_page_data_bindings_v1,
}


async def handle_public_request(
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
    detail="Unknown system public operation",
  )




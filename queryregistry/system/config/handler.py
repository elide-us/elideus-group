"""System config handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import delete_config_v1, get_config_v1, get_configs_v1, upsert_config_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_config_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get", "1"): get_config_v1,
  ("list", "1"): get_configs_v1,
  ("upsert", "1"): upsert_config_v1,
  ("delete", "1"): delete_config_v1,
}


async def handle_config_request(
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
    detail="Unknown system config operation",
  )

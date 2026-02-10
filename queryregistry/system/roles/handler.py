"""System roles handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import delete_role_v1, list_roles_v1, upsert_role_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_roles_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_roles_v1,
  ("create", "1"): upsert_role_v1,
  ("update", "1"): upsert_role_v1,
  ("delete", "1"): delete_role_v1,
}


async def handle_roles_request(
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
    detail="Unknown system roles operation",
  )

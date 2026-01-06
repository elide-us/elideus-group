"""Identity role_memberships handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request, SubdomainDispatcher
from queryregistry.models import DBRequest, DBResponse

from .services import (
  add_role_member_v1,
  list_role_members_v1,
  list_role_non_members_v1,
  remove_role_member_v1,
)

__all__ = ["handle_role_memberships_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_role_members_v1,
  ("list_non_members", "1"): list_role_non_members_v1,
  ("create", "1"): add_role_member_v1,
  ("delete", "1"): remove_role_member_v1,
}


async def handle_role_memberships_request(
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
    detail="Unknown identity role_memberships operation",
  )

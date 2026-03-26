"""Identity roles handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request, SubdomainDispatcher
from queryregistry.models import DBRequest, DBResponse

from .services import (
  add_role_member_v1,
  get_roles_v1,
  list_all_role_memberships_v1,
  list_role_members_v1,
  list_role_non_members_v1,
  remove_role_member_v1,
  set_roles_v1,
)

__all__ = ["handle_roles_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("list", "1"): list_role_members_v1,
  ("list_all", "1"): list_all_role_memberships_v1,
  ("list_non_members", "1"): list_role_non_members_v1,
  ("create", "1"): add_role_member_v1,
  ("delete", "1"): remove_role_member_v1,
  ("get_roles", "1"): get_roles_v1,
  ("set_roles", "1"): set_roles_v1,
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
    detail="Unknown identity roles operation",
  )

"""Identity roles request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import ModifyRoleMemberParams, RoleScopeParams, SetRolesParams, UserGuidParams

__all__ = [
  "create_role_membership_request",
  "delete_role_membership_request",
  "get_roles_request",
  "list_all_role_memberships_request",
  "list_role_memberships_request",
  "list_role_non_memberships_request",
  "set_roles_request",
]


def list_all_role_memberships_request() -> DBRequest:
  return DBRequest(
    op="db:identity:roles:list_all:1",
    payload={},
  )


def list_role_memberships_request(params: RoleScopeParams) -> DBRequest:
  return DBRequest(
    op="db:identity:roles:list:1",
    payload=params.model_dump(),
  )


def list_role_non_memberships_request(params: RoleScopeParams) -> DBRequest:
  return DBRequest(
    op="db:identity:roles:list_non_members:1",
    payload=params.model_dump(),
  )


def create_role_membership_request(params: ModifyRoleMemberParams) -> DBRequest:
  return DBRequest(
    op="db:identity:roles:create:1",
    payload=params.model_dump(),
  )


def delete_role_membership_request(params: ModifyRoleMemberParams) -> DBRequest:
  return DBRequest(
    op="db:identity:roles:delete:1",
    payload=params.model_dump(),
  )


def get_roles_request(params: UserGuidParams) -> DBRequest:
  return DBRequest(op="db:identity:roles:get_roles:1", payload=params.model_dump())


def set_roles_request(params: SetRolesParams) -> DBRequest:
  return DBRequest(op="db:identity:roles:set_roles:1", payload=params.model_dump())

"""Identity role_memberships request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import ModifyRoleMemberPayload, RoleScopePayload

__all__ = [
  "create_role_membership_request",
  "delete_role_membership_request",
  "list_role_memberships_request",
  "list_role_non_memberships_request",
]


def list_role_memberships_request(params: RoleScopePayload) -> DBRequest:
  return DBRequest(
    op="db:identity:role_memberships:list:1",
    payload=dict(params),
  )


def list_role_non_memberships_request(params: RoleScopePayload) -> DBRequest:
  return DBRequest(
    op="db:identity:role_memberships:list_non_members:1",
    payload=dict(params),
  )


def create_role_membership_request(params: ModifyRoleMemberPayload) -> DBRequest:
  return DBRequest(
    op="db:identity:role_memberships:create:1",
    payload=dict(params),
  )


def delete_role_membership_request(params: ModifyRoleMemberPayload) -> DBRequest:
  return DBRequest(
    op="db:identity:role_memberships:delete:1",
    payload=dict(params),
  )

"""System roles request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteRolePayload, UpsertRolePayload

__all__ = [
  "create_system_role_request",
  "delete_system_role_request",
  "list_system_roles_request",
  "update_system_role_request",
]


def list_system_roles_request() -> DBRequest:
  return DBRequest(op="db:system:roles:list:1", payload={})


def create_system_role_request(params: UpsertRolePayload) -> DBRequest:
  return DBRequest(
    op="db:system:roles:create:1",
    payload=dict(params),
  )


def update_system_role_request(params: UpsertRolePayload) -> DBRequest:
  return DBRequest(
    op="db:system:roles:update:1",
    payload=dict(params),
  )


def delete_system_role_request(params: DeleteRolePayload) -> DBRequest:
  return DBRequest(
    op="db:system:roles:delete:1",
    payload=dict(params),
  )

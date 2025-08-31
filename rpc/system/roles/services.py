from fastapi import Request
import logging
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  SystemRolesList1,
  SystemRolesRoleItem1,
  SystemRolesUpsertRole1,
  SystemRolesDeleteRole1,
)


async def system_roles_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_get_roles_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  db: DbModule = request.app.state.db
  res = await db.run("db:system:roles:list:1", {})
  roles = []
  for row in res.rows:
    roles.append(
      SystemRolesRoleItem1(
        name=row.get("name", ""),
        mask=str(row.get("mask", 0)),
        display=row.get("display"),
      )
    )
  payload = SystemRolesList1(roles=roles)
  logging.debug(
    "[system_roles_get_roles_v1] returning %d roles",
    len(roles),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_roles_upsert_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_upsert_role_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  data = SystemRolesUpsertRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:upsert_role:1", {
    "name": data.name,
    "mask": int(data.mask),
    "display": data.display,
  })
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def system_roles_delete_role_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[system_roles_delete_role_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  data = SystemRolesDeleteRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:delete_role:1", {"name": data.name})
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )

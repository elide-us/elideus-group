from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  ServiceRolesRoleItem1,
  ServiceRolesList1,
  ServiceRolesUpsertRole1,
  ServiceRolesDeleteRole1,
)


async def service_roles_get_roles_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  res = await db.run("db:system:roles:list:1", {})
  roles = [
    ServiceRolesRoleItem1(
      name=r.get("name", ""),
      mask=str(r.get("mask", "")),
      display=r.get("display"),
    )
    for r in res.rows
    if r.get("name") != "ROLE_REGISTERED"
  ]
  payload = ServiceRolesList1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def service_roles_upsert_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesUpsertRole1(**(rpc_request.payload or {}))
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


async def service_roles_delete_role_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRolesDeleteRole1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:security:roles:delete_role:1", {"name": data.name})
  auth: AuthModule = request.app.state.auth
  await auth.refresh_role_cache()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


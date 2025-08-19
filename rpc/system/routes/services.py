from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  SystemRoutesRouteItem1,
  SystemRoutesList1,
  SystemRoutesDeleteRoute1,
)


async def system_routes_get_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  db: DbModule = request.app.state.db
  auth: AuthModule = request.app.state.auth
  res = await db.run(rpc_request.op, {})
  routes = []
  for row in res.rows:
    mask = int(row.get("element_roles", 0))
    roles = auth.mask_to_names(mask)
    item = SystemRoutesRouteItem1(
      path=row.get("element_path", ""),
      name=row.get("element_name", ""),
      icon=row.get("element_icon"),
      sequence=int(row.get("element_sequence", 0)),
      required_roles=roles,
    )
    routes.append(item)
  payload = SystemRoutesList1(routes=routes)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_routes_upsert_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  payload = SystemRoutesRouteItem1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  auth: AuthModule = request.app.state.auth
  mask = auth.names_to_mask(payload.required_roles)
  await db.run(rpc_request.op, {
    "path": payload.path,
    "name": payload.name,
    "icon": payload.icon,
    "sequence": payload.sequence,
    "roles": mask,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_routes_delete_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  payload = SystemRoutesDeleteRoute1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {"path": payload.path})
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


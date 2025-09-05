from fastapi import Request
import logging

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from .models import (
  ServiceRoutesRouteItem1,
  ServiceRoutesList1,
  ServiceRoutesDeleteRoute1,
)


async def service_routes_get_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[service_routes_get_routes_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  db: DbModule = request.app.state.db
  auth: AuthModule = request.app.state.auth
  res = await db.run("db:service:routes:get_routes:1", {})
  routes = []
  for row in res.rows:
    mask = int(row.get("element_roles", 0))
    roles = auth.mask_to_names(mask)
    item = ServiceRoutesRouteItem1(
      path=row.get("element_path", ""),
      name=row.get("element_name", ""),
      icon=row.get("element_icon"),
      sequence=int(row.get("element_sequence", 0)),
      required_roles=roles,
    )
    routes.append(item)
  payload = ServiceRoutesList1(routes=routes)
  logging.debug(
    "[service_routes_get_routes_v1] returning %d routes",
    len(routes),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def service_routes_upsert_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[service_routes_upsert_route_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  payload = ServiceRoutesRouteItem1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  auth: AuthModule = request.app.state.auth
  mask = auth.names_to_mask(payload.required_roles)
  await db.run("db:service:routes:upsert_route:1", {
    "path": payload.path,
    "name": payload.name,
    "icon": payload.icon,
    "sequence": payload.sequence,
    "roles": mask,
  })
  logging.debug(
    "[service_routes_upsert_route_v1] upserted route %s",
    payload.path,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def service_routes_delete_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[service_routes_delete_route_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  payload = ServiceRoutesDeleteRoute1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:service:routes:delete_route:1", {"path": payload.path})
  logging.debug(
    "[service_routes_delete_route_v1] deleted route %s",
    payload.path,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


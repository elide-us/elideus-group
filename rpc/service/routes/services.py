from fastapi import Request
import logging

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.service_routes_module import ServiceRoutesModule
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
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  payload = await module.get_routes(auth_ctx.user_guid, auth_ctx.roles)
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
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  await module.upsert_route(auth_ctx.user_guid, auth_ctx.roles, payload)
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
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  await module.delete_route(auth_ctx.user_guid, auth_ctx.roles, payload.path)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


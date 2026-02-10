from fastapi import Request
import logging

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.models.service_routes import (
  ServiceRouteCollection,
  ServiceRouteDelete,
  ServiceRouteItem,
)
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
  payload: ServiceRouteCollection = await module.get_routes(
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  rpc_payload = ServiceRoutesList1(
    routes=[ServiceRoutesRouteItem1(**route.to_dict()) for route in payload.routes],
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=rpc_payload.model_dump(),
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
  rpc_payload = ServiceRoutesRouteItem1(**(rpc_request.payload or {}))
  internal_payload = ServiceRouteItem.from_dict(rpc_payload.model_dump())
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  result = await module.upsert_route(
    auth_ctx.user_guid,
    auth_ctx.roles,
    internal_payload,
  )
  rpc_result = ServiceRoutesRouteItem1(**result.to_dict())
  return RPCResponse(
    op=rpc_request.op,
    payload=rpc_result.model_dump(),
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
  rpc_payload = ServiceRoutesDeleteRoute1(**(rpc_request.payload or {}))
  internal_payload = ServiceRouteDelete.from_dict(rpc_payload.model_dump())
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  result = await module.delete_route(
    auth_ctx.user_guid,
    auth_ctx.roles,
    internal_payload.path,
  )
  rpc_result = ServiceRoutesDeleteRoute1(**result.to_dict())
  return RPCResponse(
    op=rpc_request.op,
    payload=rpc_result.model_dump(),
    version=rpc_request.version,
  )


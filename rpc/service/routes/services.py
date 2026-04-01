from fastapi import Request

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
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  routes = await module.get_routes(auth_ctx.user_guid, auth_ctx.roles)
  payload = ServiceRoutesList1(routes=[ServiceRoutesRouteItem1(**r) for r in routes])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_routes_upsert_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = ServiceRoutesRouteItem1(**(rpc_request.payload or {}))
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  result: ServiceRoutesRouteItem1 = await module.upsert_route(auth_ctx.user_guid, auth_ctx.roles, data.model_dump())
  payload = ServiceRoutesRouteItem1(**result)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_routes_delete_route_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = ServiceRoutesDeleteRoute1(**(rpc_request.payload or {}))
  module: ServiceRoutesModule = request.app.state.service_routes
  await module.on_ready()
  result: ServiceRoutesDeleteRoute1 = await module.delete_route(auth_ctx.user_guid, auth_ctx.roles, data.path)
  payload = ServiceRoutesDeleteRoute1(**result)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

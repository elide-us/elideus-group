from __future__ import annotations

import logging

from fastapi import HTTPException, Request

from typing import TYPE_CHECKING

from rpc.helpers import unbox_request
from server.models import RPCResponse
from .models import (
  ServiceRoutesRouteItem1,
  ServiceRoutesList1,
  ServiceRoutesDeleteRoute1,
)

if TYPE_CHECKING:
  from server.modules.service_routes_module import ServiceRoutesModule


async def service_routes_get_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[service_routes_get_routes_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  routes_mod: ServiceRoutesModule = request.app.state.service_routes
  route_dicts = await routes_mod.list_routes()
  routes = [ServiceRoutesRouteItem1(**route) for route in route_dicts]
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
  routes_mod: ServiceRoutesModule = request.app.state.service_routes
  try:
    route_dict = await routes_mod.upsert_route(
      path=payload.path,
      name=payload.name,
      icon=payload.icon,
      sequence=payload.sequence,
      required_roles=payload.required_roles,
    )
  except KeyError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = ServiceRoutesRouteItem1(**route_dict)
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
  routes_mod: ServiceRoutesModule = request.app.state.service_routes
  result = await routes_mod.delete_route(payload.path)
  payload = ServiceRoutesDeleteRoute1(**result)
  logging.debug(
    "[service_routes_delete_route_v1] deleted route %s",
    payload.path,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


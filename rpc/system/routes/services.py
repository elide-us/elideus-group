from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.routes.models import (
  SystemRoutesList2,
  SystemRouteItem,
  SystemRouteUpdate2,
  SystemRouteDelete2,
)
from server.modules.database_provider import DatabaseProvider
from server.helpers.roles import mask_to_names, names_to_mask


async def list_routes_v2(request: Request) -> RPCResponse:
  db: DatabaseProvider = request.app.state.mssql
  rows = await db.list_routes()
  routes = [
    SystemRouteItem(
      path=r['element_path'],
      name=r['element_name'],
      icon=r['element_icon'],
      sequence=r['element_sequence'],
      requiredRoles=mask_to_names(int(r.get('element_roles') or 0)),
    )
    for r in rows
  ]
  payload = SystemRoutesList2(routes=routes)
  return RPCResponse(op='urn:system:routes:list:2', payload=payload, version=2)


async def set_route_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteUpdate2(**(rpc_request.payload or {}))
  db: DatabaseProvider = request.app.state.mssql
  mask = names_to_mask(data.requiredRoles)
  await db.set_route(data.path, data.name, data.icon, mask, data.sequence)
  return await list_routes_v2(request)


async def delete_route_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteDelete2(**(rpc_request.payload or {}))
  db: DatabaseProvider = request.app.state.mssql
  await db.delete_route(data.path)
  return await list_routes_v2(request)

from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.routes.models import (
  SystemRoutesList1,
  SystemRoutesList2,
  SystemRouteItem,
  SystemRouteUpdate1,
  SystemRouteUpdate2,
  SystemRouteDelete1,
  SystemRouteDelete2,
)
from server.modules.database_module import DatabaseModule
from server.modules.mssql_module import MSSQLModule
from server.helpers.roles import mask_to_names, names_to_mask

async def list_routes_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_routes()
  routes = [
    SystemRouteItem(
      path=r['path'],
      name=r['name'],
      icon=r['icon'],
      sequence=r['sequence'],
      requiredRoles=mask_to_names(int(r['required_roles'] or 0)),
    )
    for r in rows
  ]
  payload = SystemRoutesList1(routes=routes)
  return RPCResponse(op='urn:system:routes:list:1', payload=payload, version=1)

async def set_route_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  mask = names_to_mask(data.requiredRoles)
  await db.set_route(data.path, data.name, data.icon, mask, data.sequence)
  return await list_routes_v1(request)

async def delete_route_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_route(data.path)
  return await list_routes_v1(request)


async def list_routes_v2(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
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
  db: MSSQLModule = request.app.state.mssql
  mask = names_to_mask(data.requiredRoles)
  await db.set_route(data.path, data.name, data.icon, mask, data.sequence)
  return await list_routes_v2(request)


async def delete_route_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteDelete2(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_route(data.path)
  return await list_routes_v2(request)

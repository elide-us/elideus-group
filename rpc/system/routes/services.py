from fastapi import Request

from rpc.helpers import (get_rpcrequest_from_request, mask_to_names,
                         names_to_mask)
from rpc.models import RPCRequest, RPCResponse
from rpc.system.routes.models import (SystemRouteDelete1, SystemRouteItem,
                                      SystemRoutesList1, SystemRouteUpdate1)
from server.modules.mssql_module import MSSQLModule


async def list_routes_v1(request: Request) -> RPCResponse:
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
  payload = SystemRoutesList1(routes=routes)
  return RPCResponse(op='urn:system:routes:list:1', payload=payload, version=1)

async def set_route_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  data = SystemRouteUpdate1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  mask = names_to_mask(data.requiredRoles)
  await db.set_route(data.path, data.name, data.icon, mask, data.sequence)
  return await list_routes_v1(request)

async def delete_route_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)
  
  data = SystemRouteDelete1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_route(data.path)
  return await list_routes_v1(request)

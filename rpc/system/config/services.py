from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.config.models import (
  SystemConfigList1,
  ConfigItem,
  SystemConfigUpdate1,
  SystemConfigDelete1
)
from server.modules.mssql_module import MSSQLModule
from rpc.helpers import get_rpcrequest_from_request

async def list_config_v1(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_config()
  items = [ConfigItem(key=r['key'], value=str(r['value'])) for r in rows]
  payload = SystemConfigList1(items=items)
  return RPCResponse(op='urn:system:config:list:1', payload=payload, version=1)

async def set_config_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemConfigUpdate1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.set_config_value(data.key, str(data.value))
  return await list_config_v1(request)

async def delete_config_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemConfigDelete1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_config_value(data.key)
  return await list_config_v1(request)

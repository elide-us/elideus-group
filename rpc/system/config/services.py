from fastapi import Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.config.models import (SystemConfigItem1, SystemConfigDelete1,
                                      SystemConfigList1, SystemConfigUpdate1)
from server.modules.mssql_module import MSSQLModule


async def system_config_get_configs_v1(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_config()
  items = [SystemConfigItem1(key=r['key'], value=str(r['value'])) for r in rows]
  payload = SystemConfigList1(items=items)
  return RPCResponse(op='urn:system:config:list:1', payload=payload, version=1)

async def system_config_set_config_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemConfigItem1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.set_config_value(data.key, str(data.value))
  return await system_config_get_configs_v1(request)

async def system_config_delete_config_v1(request: Request) -> RPCResponse:
  rpc_request: RPCRequest = get_rpcrequest_from_request(request)

  data = SystemConfigItem1(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_config_value(data.key)
  return await system_config_get_configs_v1(request)

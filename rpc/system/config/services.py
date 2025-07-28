from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.config.models import (
  SystemConfigList1,
  ConfigItem,
  SystemConfigUpdate1,
  SystemConfigDelete1,
  SystemConfigList2,
  SystemConfigUpdate2,
  SystemConfigDelete2,
)
from server.modules.mssql_module import MSSQLModule


async def list_config_v2(request: Request) -> RPCResponse:
  db: MSSQLModule = request.app.state.mssql
  rows = await db.list_config()
  items = [ConfigItem(key=r['element_key'], value=str(r['element_value'])) for r in rows]
  payload = SystemConfigList2(items=items)
  return RPCResponse(op='urn:system:config:list:2', payload=payload, version=2)

async def set_config_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemConfigUpdate2(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.set_config_value(data.key, str(data.value))
  return await list_config_v2(request)

async def delete_config_v2(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemConfigDelete2(**(rpc_request.payload or {}))
  db: MSSQLModule = request.app.state.mssql
  await db.delete_config_value(data.key)
  return await list_config_v2(request)

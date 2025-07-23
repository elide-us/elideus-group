from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.config.models import SystemConfigList1, ConfigItem, SystemConfigUpdate1, SystemConfigDelete1
from server.modules.database_module import DatabaseModule

async def list_config_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_config()
  items = [ConfigItem(key=r['key'], value=str(r['value'])) for r in rows]
  payload = SystemConfigList1(items=items)
  return RPCResponse(op='urn:system:config:list:1', payload=payload, version=1)

async def set_config_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemConfigUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.set_config_value(data.key, str(data.value))
  return await list_config_v1(request)

async def delete_config_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemConfigDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_config_value(data.key)
  return await list_config_v1(request)

from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.admin.config.models import AdminConfigList1, ConfigItem, AdminConfigUpdate1, AdminConfigDelete1
from server.modules.database_module import DatabaseModule

async def list_config_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_config()
  items = [ConfigItem(key=r['key'], value=r['value']) for r in rows]
  payload = AdminConfigList1(items=items)
  return RPCResponse(op='urn:admin:config:list:1', payload=payload, version=1)

async def set_config_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = AdminConfigUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.set_config_value(data.key, data.value)
  return await list_config_v1(request)

async def delete_config_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = AdminConfigDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_config_value(data.key)
  return await list_config_v1(request)

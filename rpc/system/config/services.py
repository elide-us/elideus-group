from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.system_config_module import SystemConfigModule
from .models import (
  SystemConfigConfigItem1,
  SystemConfigDeleteConfig1,
  SystemConfigList1,
)

async def system_config_get_configs_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: SystemConfigModule = request.app.state.system_config
  await module.on_ready()
  module_payload = await module.get_configs(auth_ctx.user_guid, auth_ctx.roles)
  payload = SystemConfigList1(
    items=[
      SystemConfigConfigItem1(key=item.key, value=item.value)
      for item in module_payload.items
    ],
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def system_config_upsert_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = SystemConfigConfigItem1(**(rpc_request.payload or {}))
  module: SystemConfigModule = request.app.state.system_config
  await module.on_ready()
  module_payload = await module.upsert_config(
    auth_ctx.user_guid,
    auth_ctx.roles,
    input_payload.key,
    input_payload.value,
  )
  payload = SystemConfigConfigItem1(
    key=module_payload.key,
    value=module_payload.value,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def system_config_delete_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = SystemConfigDeleteConfig1(**(rpc_request.payload or {}))
  module: SystemConfigModule = request.app.state.system_config
  await module.on_ready()
  module_payload = await module.delete_config(
    auth_ctx.user_guid,
    auth_ctx.roles,
    input_payload.key,
  )
  payload = SystemConfigDeleteConfig1(key=module_payload.key)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

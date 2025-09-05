from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.system_config_module import SystemConfigModule
from .models import (
  SystemConfigConfigItem1,
  SystemConfigDeleteConfig1,
)

async def system_config_get_configs_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  config_mod: SystemConfigModule = request.app.state.system_config
  payload = await config_mod.get_configs(auth_ctx.user_guid, auth_ctx.roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def system_config_upsert_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = SystemConfigConfigItem1(**(rpc_request.payload or {}))
  config_mod: SystemConfigModule = request.app.state.system_config
  payload = await config_mod.upsert_config(
    auth_ctx.user_guid,
    auth_ctx.roles,
    input_payload.key,
    input_payload.value,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def system_config_delete_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = SystemConfigDeleteConfig1(**(rpc_request.payload or {}))
  config_mod: SystemConfigModule = request.app.state.system_config
  payload = await config_mod.delete_config(
    auth_ctx.user_guid,
    auth_ctx.roles,
    input_payload.key,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

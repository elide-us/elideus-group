from fastapi import HTTPException, Request
import logging

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  SystemConfigConfigItem1,
  SystemConfigList1,
  SystemConfigDeleteConfig1,
)


async def system_config_get_configs_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  logging.debug(
    "[system_config_get_configs_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    logging.debug(
      "[system_config_get_configs_v1] forbidden for user=%s",
      auth_ctx.user_guid,
    )
    raise HTTPException(status_code=403, detail="Forbidden")
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, {})
  items = []
  for row in res.rows:
    item = SystemConfigConfigItem1(
      key=row.get("element_key", ""),
      value=row.get("element_value", ""),
    )
    items.append(item)
  payload = SystemConfigList1(items=items)
  logging.debug(
    "[system_config_get_configs_v1] returning %d items",
    len(items),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_config_upsert_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  logging.debug(
    "[system_config_upsert_config_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    logging.debug(
      "[system_config_upsert_config_v1] forbidden for user=%s",
      auth_ctx.user_guid,
    )
    raise HTTPException(status_code=403, detail="Forbidden")
  payload = SystemConfigConfigItem1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {"key": payload.key, "value": payload.value})
  logging.debug(
    "[system_config_upsert_config_v1] upserted config %s",
    payload.key,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def system_config_delete_config_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  logging.debug(
    "[system_config_delete_config_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  if "ROLE_SYSTEM_ADMIN" not in auth_ctx.roles:
    logging.debug(
      "[system_config_delete_config_v1] forbidden for user=%s",
      auth_ctx.user_guid,
    )
    raise HTTPException(status_code=403, detail="Forbidden")
  payload = SystemConfigDeleteConfig1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {"key": payload.key})
  logging.debug(
    "[system_config_delete_config_v1] deleted config %s",
    payload.key,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

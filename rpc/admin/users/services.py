from fastapi import HTTPException, Request

from importlib import import_module
import gc

from rpc.helpers import get_rpcrequest_from_request
from rpc.users.profile.models import UsersProfileProfile1
from server.modules.db_module import DbModule
from server.modules.storage_module import StorageModule
from .models import AdminUsersGuid1, AdminUsersSetCredits1


async def admin_users_get_profile_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_ADMIN_SUPPORT" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = AdminUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  res = await db.run("db:users:profile:get_profile:1", {"guid": data.userGuid})
  if not res.rows:
    raise HTTPException(status_code=404, detail="Profile not found")
  row = res.rows[0]
  row["guid"] = str(row.get("guid", ""))
  auth_providers = row.get("auth_providers")
  if isinstance(auth_providers, str):
    import json
    row["auth_providers"] = json.loads(auth_providers) if auth_providers else []
  profile = UsersProfileProfile1(**row)
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )


async def admin_users_set_credits_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_ADMIN_SUPPORT" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = AdminUsersSetCredits1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(
    "db:admin:users:set_credits:1",
    {"guid": data.userGuid, "credits": data.credits},
  )
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def admin_users_reset_display_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_ADMIN_SUPPORT" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = AdminUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:admin:users:reset_display:1", {"guid": data.userGuid})
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def admin_users_enable_storage_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_ADMIN_SUPPORT" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  data = AdminUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run("db:admin:users:enable_storage:1", {"guid": data.userGuid})
  storage: StorageModule = request.app.state.storage
  await storage.ensure_user_folder(data.userGuid)
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


def _get_rpc_response_class():
  bases = []
  for obj in gc.get_objects():
    if isinstance(obj, type) and obj.__name__ == "RPCResponse":
      bases.append(obj)
  if not bases:
    bases.append(import_module("rpc.models").RPCResponse)
  bases = tuple(dict.fromkeys(bases))
  return type("RPCResponseCompat", bases, {})


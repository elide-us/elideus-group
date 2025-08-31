from importlib import import_module
import gc
from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from rpc.users.profile.models import UsersProfileProfile1
from server.modules.db_module import DbModule
from server.modules.storage_module import StorageModule
from .models import SupportUsersGuid1, SupportUsersSetCredits1


async def get_profile(db: DbModule, guid: str) -> UsersProfileProfile1:
  res = await db.run("db:users:profile:get_profile:1", {"guid": guid})
  if not res.rows:
    raise HTTPException(status_code=404, detail="Profile not found")
  row = res.rows[0]
  row["guid"] = str(row.get("guid", ""))
  auth_providers = row.get("auth_providers")
  if isinstance(auth_providers, str):
    import json
    row["auth_providers"] = json.loads(auth_providers) if auth_providers else []
  return UsersProfileProfile1(**row)


async def set_credits(db: DbModule, guid: str, credits: int) -> None:
  await db.run(
    "db:support:users:set_credits:1",
    {"guid": guid, "credits": credits},
  )


async def reset_display(db: DbModule, guid: str) -> None:
  await db.run("db:support:users:reset_display:1", {"guid": guid})


async def enable_storage(db: DbModule, storage: StorageModule, guid: str) -> None:
  await db.run("db:support:users:enable_storage:1", {"guid": guid})
  await storage.ensure_user_folder(guid)


async def support_users_get_profile_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  profile = await get_profile(db, data.userGuid)
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )


async def support_users_set_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersSetCredits1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await set_credits(db, data.userGuid, data.credits)
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def support_users_reset_display_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await reset_display(db, data.userGuid)
  RPCResponse = _get_rpc_response_class()
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def support_users_enable_storage_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = SupportUsersGuid1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  storage: StorageModule = request.app.state.storage
  await enable_storage(db, storage, data.userGuid)
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
    bases.append(import_module("server.models").RPCResponse)
  bases = tuple(dict.fromkeys(bases))
  return type("RPCResponseCompat", bases, {})


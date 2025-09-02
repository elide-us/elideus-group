from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import AuthProvidersUnlinkLastProvider1


async def auth_providers_unlink_last_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = AuthProvidersUnlinkLastProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  await db.run(
    rpc_request.op,
    {"guid": payload.guid, "provider": payload.provider},
  )
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)

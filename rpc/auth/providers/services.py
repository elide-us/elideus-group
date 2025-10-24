from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.oauth_module import OauthModule

from .models import AuthProvidersUnlinkLastProvider1


async def auth_providers_unlink_last_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = AuthProvidersUnlinkLastProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  oauth_module: OauthModule | None = getattr(request.app.state, "oauth", None)
  if not oauth_module:
    raise HTTPException(status_code=503, detail="oauth module unavailable")
  await oauth_module.on_ready()
  await oauth_module.unlink_last_provider_record(payload.guid, payload.provider)
  return RPCResponse(op=rpc_request.op, payload={"ok": True}, version=rpc_request.version)

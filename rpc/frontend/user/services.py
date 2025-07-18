from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.user.models import FrontendUserSetDisplayName1
from server.modules.database_module import DatabaseModule
from server.modules.auth_module import AuthModule

async def set_display_name_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = FrontendUserSetDisplayName1(**(rpc_request.payload or {}))
  auth: AuthModule = request.app.state.auth
  db: DatabaseModule = request.app.state.database
  data = await auth.decode_bearer_token(payload.bearerToken)
  await db.update_display_name(data["guid"], payload.displayName)
  return RPCResponse(op="urn:frontend:user:set_display_name:1", payload=None, version=1)

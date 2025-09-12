import logging

from fastapi import HTTPException, Request, status
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.modules.auth_module import AuthModule
from .models import AuthDiscordOauthLoginPayload1


async def auth_discord_oauth_login_v1(request: Request):
  """Placeholder Discord OAuth login handler.

  This endpoint will eventually exchange an authorization code for tokens and
  create a user session. The current implementation only validates that the
  Discord provider is configured and ensures the payload shape is correct.
  """
  rpc_request, _, _ = await unbox_request(request)
  try:
    AuthDiscordOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  auth: AuthModule = request.app.state.auth
  if "discord" not in getattr(auth, "providers", {}):
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Discord provider not configured")
  raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Discord OAuth login not implemented")

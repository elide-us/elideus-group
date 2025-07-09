from fastapi import Request
from rpc.models import RPCResponse, RPCRequest
from rpc.auth.microsoft.models import AuthMicrosoftLoginData1

async def user_login_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}

  # Stubbed authentication logic. In a future implementation this will
  # verify the Microsoft tokens and load or create the user from a database.
  login_data = AuthMicrosoftLoginData1(
    bearerToken="stub-token",
    defaultProvider="microsoft",
    username=payload.get("username", "stub-user"),
    email=payload.get("email", "stub@example.com"),
    backupEmail=payload.get("backupEmail"),
    profilePicture=payload.get("profilePicture"),
    credits=0,
  )

  return RPCResponse(op="urn:auth:microsoft:login_data:1", payload=login_data, version=1)

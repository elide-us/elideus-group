from fastapi import Request, HTTPException
import logging
from rpc.admin.handler import handle_admin_request
from rpc.auth.handler import handle_auth_request
from rpc.models import RPCRequest, RPCResponse
from rpc.views import format_response

async def handle_rpc_request(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  parts = rpc_request.op.split(":")

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  context = None
  variant = None
  if len(parts) >= 4 and parts[-3] == "view":
    context = parts[-2]
    variant = parts[-1]
    core_parts = parts[:-3]
  elif len(parts) >= 3 and parts[-2] == "view":
    context = parts[-1]
    core_parts = parts[:-2]
  else:
    core_parts = parts

  try:
    match core_parts[1:]:
      case ["admin", *rest]:
        response = await handle_admin_request(rest, request)
      case ["auth", *rest]:
        response = await handle_auth_request(rest, rpc_request, request)
      case _:
        raise HTTPException(status_code=404, detail="Unknown RPC domain")
    response = format_response(response, context, variant)
    if context:
      response.op = rpc_request.op
    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise

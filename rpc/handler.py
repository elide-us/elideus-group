import logging

from fastapi import HTTPException, Request

from rpc import HANDLERS
from rpc.helpers import unbox_request
from rpc.models import RPCResponse


async def handle_rpc_request(request: Request) -> RPCResponse:
  rpc_request, _, parts = await unbox_request(request)

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  try:
    domain = parts[1]
    remainder = parts[2:]

    handler = HANDLERS.get(domain)
    if not handler:
      raise HTTPException(status_code=404, detail="Unknown RPC domain")
    response = await handler(remainder, request)

    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise


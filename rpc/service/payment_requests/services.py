"""Service payment requests RPC service functions."""

from __future__ import annotations

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import PaymentRequestCreate1, PaymentRequestCreateResult1


async def service_payment_requests_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = PaymentRequestCreate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    result = await module.create_payment_request(payload.model_dump(), auth_ctx.user_guid)
  except ValueError as exc:
    detail = str(exc)
    if detail.startswith("Unknown vendor:"):
      raise HTTPException(status_code=404, detail=detail) from exc
    raise HTTPException(status_code=400, detail=detail) from exc
  response = PaymentRequestCreateResult1(**result)
  return RPCResponse(
    op=rpc_request.op,
    payload=response.model_dump(),
    version=rpc_request.version,
  )

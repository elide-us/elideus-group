from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  CreditLotConsume1,
  CreditLotConsumeResult1,
  CreditLotCreate1,
  CreditLotEventItem1,
  CreditLotEventList1,
  CreditLotExpire1,
  CreditLotGet1,
  CreditLotItem1,
  CreditLotList1,
  CreditLotListByUser1,
  CreditLotListEvents1,
  CreditLotWalletBalance1,
  CreditLotWalletResult1,
)


async def finance_credit_lots_list_by_user_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotListByUser1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_lots_by_user(input_payload.users_guid)
  payload = CreditLotList1(lots=[CreditLotItem1(**lot) for lot in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_lot(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Credit lot not found")
  payload = CreditLotItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotCreate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.create_lot(
      users_guid=input_payload.users_guid,
      source_type=input_payload.source_type,
      credits=input_payload.credits,
      total_paid=input_payload.total_paid,
      currency=input_payload.currency,
      expires_at=input_payload.expires_at,
      source_id=input_payload.source_id,
      actor_guid=auth_ctx.user_guid,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = CreditLotItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_consume_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotConsume1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    result = await module.consume_credits(
      users_guid=input_payload.users_guid,
      credits_needed=input_payload.credits_needed,
      service_type=input_payload.service_type,
      description=input_payload.description,
      periods_guid=input_payload.periods_guid,
      actor_guid=auth_ctx.user_guid,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = CreditLotConsumeResult1(**result)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_expire_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotExpire1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.expire_lot(input_payload.recid, actor_guid=auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = CreditLotItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_list_events_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotListEvents1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_lot_events(input_payload.lots_recid)
  payload = CreditLotEventList1(events=[CreditLotEventItem1(**event) for event in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_credit_lots_wallet_balance_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = CreditLotWalletBalance1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  balance = await module.get_wallet_balance(input_payload.users_guid)
  payload = CreditLotWalletResult1(users_guid=input_payload.users_guid, balance=balance)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinancePeriodsBlockerItem1,
  FinancePeriodsBlockerList1,
  FinancePeriodsClose1,
  FinancePeriodsDelete1,
  FinancePeriodsGenerateCalendar1,
  FinancePeriodsGet1,
  FinancePeriodsItem1,
  FinancePeriodsList1,
  FinancePeriodsListByYear1,
  FinancePeriodsListCloseBlockers1,
  FinancePeriodsLock1,
  FinancePeriodsReopen1,
  FinancePeriodsUnlock1,
  FinancePeriodsUpsert1,
)


async def finance_periods_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_periods()
  periods = [FinancePeriodsItem1(**row) for row in rows]
  payload = FinancePeriodsList1(periods=periods)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_list_by_year_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsListByYear1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_periods_by_year(input_payload.year)
  periods = [FinancePeriodsItem1(**row) for row in rows]
  payload = FinancePeriodsList1(periods=periods)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_period(input_payload.guid)
  if not row:
    raise HTTPException(status_code=404, detail="Period not found")
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_close_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsClose1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.close_period(input_payload.guid, auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_reopen_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsReopen1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.reopen_period(input_payload.guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_lock_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsLock1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.lock_period(input_payload.guid, auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_unlock_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsUnlock1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.unlock_period(input_payload.guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_list_close_blockers_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsListCloseBlockers1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.list_period_close_blockers(input_payload.guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  blockers = [FinancePeriodsBlockerItem1(**row) for row in rows]
  payload = FinancePeriodsBlockerList1(blockers=blockers)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_period(input_payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = FinancePeriodsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_period(input_payload.guid)
  payload = FinancePeriodsDelete1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_periods_generate_calendar_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsGenerateCalendar1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.generate_calendar(input_payload.fiscal_year, input_payload.start_date)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  periods = [FinancePeriodsItem1(**row) for row in rows]
  payload = FinancePeriodsList1(periods=periods)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

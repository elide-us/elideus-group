from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinancePeriodsDelete1,
  FinancePeriodsGenerateCalendar1,
  FinancePeriodsGet1,
  FinancePeriodsItem1,
  FinancePeriodsList1,
  FinancePeriodsListByYear1,
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


async def finance_periods_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinancePeriodsUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.upsert_period(input_payload.model_dump())
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
  rows = await module.generate_calendar(input_payload.fiscal_year, input_payload.start_date)
  periods = [FinancePeriodsItem1(**row) for row in rows]
  payload = FinancePeriodsList1(periods=periods)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

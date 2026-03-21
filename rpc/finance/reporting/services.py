from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  CreditLotSummaryFilter1,
  CreditLotSummaryList1,
  JournalSummaryFilter1,
  JournalSummaryList1,
  PeriodStatusFilter1,
  PeriodStatusList1,
  TrialBalanceFilter1,
  TrialBalanceList1,
)


async def finance_reporting_trial_balance_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = TrialBalanceFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.trial_balance(payload.fiscal_year, payload.period_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = TrialBalanceList1(rows=rows)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_journal_summary_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = JournalSummaryFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.journal_summary(payload.journal_status, payload.fiscal_year, payload.periods_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = JournalSummaryList1(journals=rows)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_period_status_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = PeriodStatusFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.period_status(payload.fiscal_year)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = PeriodStatusList1(periods=rows)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_credit_lot_summary_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = CreditLotSummaryFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    rows = await module.credit_lot_summary(payload.users_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = CreditLotSummaryList1(lots=rows)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)

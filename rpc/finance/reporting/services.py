from fastapi import Request

from queryregistry.finance.reporting import (
  credit_lot_summary_request,
  journal_summary_request,
  period_status_request,
  trial_balance_request,
)
from queryregistry.finance.reporting.models import (
  CreditLotSummaryParams,
  JournalSummaryParams,
  PeriodStatusParams,
  TrialBalanceParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

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
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    trial_balance_request(
      TrialBalanceParams(
        fiscal_year=payload.fiscal_year,
        period_guid=payload.period_guid,
      ),
    ),
  )
  response_payload = TrialBalanceList1(rows=(result.rows or []))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_journal_summary_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = JournalSummaryFilter1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    journal_summary_request(
      JournalSummaryParams(
        journal_status=payload.journal_status,
        fiscal_year=payload.fiscal_year,
        periods_guid=payload.periods_guid,
      ),
    ),
  )
  response_payload = JournalSummaryList1(journals=(result.rows or []))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_period_status_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = PeriodStatusFilter1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    period_status_request(
      PeriodStatusParams(
        fiscal_year=payload.fiscal_year,
      ),
    ),
  )
  response_payload = PeriodStatusList1(periods=(result.rows or []))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_reporting_credit_lot_summary_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = CreditLotSummaryFilter1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    credit_lot_summary_request(
      CreditLotSummaryParams(
        users_guid=payload.users_guid,
      ),
    ),
  )
  response_payload = CreditLotSummaryList1(lots=(result.rows or []))
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)

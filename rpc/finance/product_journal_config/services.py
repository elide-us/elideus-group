from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from .models import (
  FinanceProductJournalConfigActivate1,
  FinanceProductJournalConfigApprove1,
  FinanceProductJournalConfigClose1,
  FinanceProductJournalConfigFilter1,
  FinanceProductJournalConfigGet1,
  FinanceProductJournalConfigItem1,
  FinanceProductJournalConfigList1,
  FinanceProductJournalConfigUpsert1,
)


async def _require_role(request: Request, user_guid: str, role_name: str, detail: str) -> None:
  module: AuthModule = request.app.state.module
  required_mask = module.roles.get(role_name, 0)
  if required_mask and not await module.user_has_role(user_guid, required_mask):
    raise HTTPException(status_code=403, detail=detail)


async def finance_product_journal_config_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinanceProductJournalConfigFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_product_journal_configs(
    category=payload.category,
    periods_guid=payload.periods_guid,
    status=payload.status,
  )
  response_payload = FinanceProductJournalConfigList1(
    configs=[FinanceProductJournalConfigItem1(**row) for row in rows]
  )
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_product_journal_config_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinanceProductJournalConfigGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_product_journal_config(payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Product journal config not found")
  response_payload = FinanceProductJournalConfigItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_product_journal_config_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_role(request, auth_ctx.user_guid, "ROLE_FINANCE_APPR", "Accounting Manager role required")
  payload = FinanceProductJournalConfigUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_product_journal_config(payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinanceProductJournalConfigItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_product_journal_config_approve_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_role(request, auth_ctx.user_guid, "ROLE_FINANCE_APPR", "Accounting Manager role required")
  payload = FinanceProductJournalConfigApprove1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.approve_product_journal_config(payload.recid, auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinanceProductJournalConfigItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_product_journal_config_activate_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_role(request, auth_ctx.user_guid, "ROLE_FINANCE_ADMIN", "Finance Admin role required")
  payload = FinanceProductJournalConfigActivate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.activate_product_journal_config(payload.recid, auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinanceProductJournalConfigItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_product_journal_config_close_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_role(request, auth_ctx.user_guid, "ROLE_FINANCE_APPR", "Accounting Manager role required")
  payload = FinanceProductJournalConfigClose1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.close_product_journal_config(payload.recid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinanceProductJournalConfigItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)

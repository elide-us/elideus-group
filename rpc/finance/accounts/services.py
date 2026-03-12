from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  FinanceAccountsDelete1,
  FinanceAccountsGet1,
  FinanceAccountsItem1,
  FinanceAccountsList1,
  FinanceAccountsListChildren1,
  FinanceAccountsUpsert1,
)


async def finance_accounts_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_accounts()
  payload = FinanceAccountsList1(accounts=[FinanceAccountsItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_accounts_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceAccountsGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_account(input_payload.guid)
  if not row:
    raise HTTPException(status_code=404, detail="Account not found")
  payload = FinanceAccountsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_accounts_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceAccountsUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.upsert_account(input_payload.model_dump())
  payload = FinanceAccountsItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_accounts_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceAccountsDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_account(input_payload.guid)
  payload = FinanceAccountsDelete1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_accounts_list_children_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceAccountsListChildren1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_account_children(input_payload.parent_guid)
  payload = FinanceAccountsList1(accounts=[FinanceAccountsItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule

from .models import (
  FinanceProductDelete1,
  FinanceProductDeleteResult1,
  FinanceProductFilter1,
  FinanceProductGet1,
  FinanceProductItem1,
  FinanceProductList1,
  FinanceProductUpsert1,
)


async def _require_finance_admin(request: Request, user_guid: str) -> None:
  module: AuthModule = request.app.state.module
  required_mask = module.roles.get("ROLE_FINANCE_ADMIN", 0)
  if required_mask == 0:
    return

  if not await module.user_has_role(user_guid, required_mask):
    raise HTTPException(status_code=403, detail="Finance Admin role required")


async def finance_products_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinanceProductFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_products(category=payload.category, status=payload.status)
  response_payload = FinanceProductList1(products=[FinanceProductItem1(**row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_products_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = FinanceProductGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_product(recid=payload.recid, sku=payload.sku)
  if not row:
    raise HTTPException(status_code=404, detail="Product not found")
  response_payload = FinanceProductItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_products_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_finance_admin(request, auth_ctx.user_guid)
  payload = FinanceProductUpsert1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.upsert_product(payload.model_dump())
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = FinanceProductItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)


async def finance_products_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  await _require_finance_admin(request, auth_ctx.user_guid)
  payload = FinanceProductDelete1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.delete_product(payload.recid)
  response_payload = FinanceProductDeleteResult1(**row)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  UsersProductItem1,
  UsersProductList1,
  UsersProductPurchase1,
  UsersProductPurchaseResult1,
)


async def users_products_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  products = await module.list_products(status=1)
  user_enablements = await module.get_user_enablements(auth_ctx.user_guid)
  user_roles = await module.get_user_roles_mask(auth_ctx.user_guid)
  items = []
  for product in products:
    already_enabled = False
    enablement_key = product.get("enablement_key")
    if enablement_key == "ROLE_STORAGE":
      already_enabled = bool(user_enablements & 1)
    elif enablement_key == "ROLE_DISCORD_BOT":
      already_enabled = bool(user_roles & 0x10)
    items.append(UsersProductItem1(**{**product, "already_enabled": already_enabled}))
  payload = UsersProductList1(products=items)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def users_products_purchase_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersProductPurchase1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    result = await module.purchase_product(
      users_guid=auth_ctx.user_guid,
      sku=payload.sku,
      actor_guid=auth_ctx.user_guid,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  response_payload = UsersProductPurchaseResult1(**result)
  return RPCResponse(op=rpc_request.op, payload=response_payload.model_dump(), version=rpc_request.version)

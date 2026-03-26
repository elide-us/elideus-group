"""Service renewals RPC service functions."""

from __future__ import annotations

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.service_renewals_module import ServiceRenewalsModule

from .models import (
  ServiceRenewalsDelete1,
  ServiceRenewalsDeleteResult1,
  ServiceRenewalsItem1,
  ServiceRenewalsList1,
  ServiceRenewalsListParams1,
  ServiceRenewalsUpsert1,
)


async def service_renewals_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  params = ServiceRenewalsListParams1(**(rpc_request.payload or {}))
  module: ServiceRenewalsModule = request.app.state.service_renewals
  await module.on_ready()
  rows = await module.list_renewals(category=params.category, status=params.status)
  renewals = [ServiceRenewalsItem1(**row) for row in rows]
  payload = ServiceRenewalsList1(renewals=renewals)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def service_renewals_get_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  recid = payload.get("recid")
  module: ServiceRenewalsModule = request.app.state.service_renewals
  await module.on_ready()
  renewal_row = await module.get_renewal(recid)
  if not renewal_row:
    raise HTTPException(status_code=404, detail="Renewal not found")
  renewal = ServiceRenewalsItem1(**renewal_row)
  return RPCResponse(
    op=rpc_request.op,
    payload=renewal.model_dump(),
    version=rpc_request.version,
  )


async def service_renewals_upsert_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRenewalsUpsert1(**(rpc_request.payload or {}))
  module: ServiceRenewalsModule = request.app.state.service_renewals
  await module.on_ready()
  await module.upsert_renewal(data.model_dump())
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def service_renewals_delete_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRenewalsDelete1(**(rpc_request.payload or {}))
  module: ServiceRenewalsModule = request.app.state.service_renewals
  await module.on_ready()
  await module.delete_renewal(data.recid)
  payload = ServiceRenewalsDeleteResult1(recid=data.recid, deleted=True)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

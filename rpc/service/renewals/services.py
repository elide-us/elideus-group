"""Service renewals RPC service functions."""

from __future__ import annotations

from fastapi import HTTPException, Request

from queryregistry.system.renewals import (
  delete_renewal_request,
  get_renewal_request,
  list_renewals_request,
  upsert_renewal_request,
)
from queryregistry.system.renewals.models import (
  DeleteRenewalParams,
  GetRenewalParams,
  ListRenewalsParams,
  UpsertRenewalParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

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
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(
    list_renewals_request(
      ListRenewalsParams(category=params.category, status=params.status),
    ),
  )
  renewals = [ServiceRenewalsItem1(**row) for row in (result.rows or [])]
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
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(get_renewal_request(GetRenewalParams(recid=recid)))
  if not result.rows:
    raise HTTPException(status_code=404, detail="Renewal not found")
  renewal = ServiceRenewalsItem1(**result.rows[0])
  return RPCResponse(
    op=rpc_request.op,
    payload=renewal.model_dump(),
    version=rpc_request.version,
  )


async def service_renewals_upsert_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRenewalsUpsert1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(upsert_renewal_request(UpsertRenewalParams(**data.model_dump())))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def service_renewals_delete_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = ServiceRenewalsDelete1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(delete_renewal_request(DeleteRenewalParams(recid=data.recid)))
  payload = ServiceRenewalsDeleteResult1(recid=data.recid, deleted=True)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

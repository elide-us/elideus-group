from fastapi import Request

from queryregistry.finance.staging_account_map import (
  delete_account_map_request,
  list_account_map_request,
  upsert_account_map_request,
)
from queryregistry.finance.staging_account_map.models import (
  DeleteAccountMapParams,
  ListAccountMapParams,
  UpsertAccountMapParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  FinanceStagingAccountMapDelete1,
  FinanceStagingAccountMapDeleteResult1,
  FinanceStagingAccountMapItem1,
  FinanceStagingAccountMapList1,
  FinanceStagingAccountMapUpsert1,
)


async def finance_staging_account_map_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(list_account_map_request(ListAccountMapParams()))
  payload = FinanceStagingAccountMapList1(
    mappings=[FinanceStagingAccountMapItem1(**dict(row)) for row in (result.rows or [])]
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_staging_account_map_upsert_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceStagingAccountMapUpsert1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  result = await db.run(upsert_account_map_request(UpsertAccountMapParams(**input_payload.model_dump())))
  row = dict(result.rows[0]) if result.rows else input_payload.model_dump()
  payload = FinanceStagingAccountMapItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_staging_account_map_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = FinanceStagingAccountMapDelete1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(delete_account_map_request(DeleteAccountMapParams(recid=input_payload.recid)))
  payload = FinanceStagingAccountMapDeleteResult1(recid=input_payload.recid, deleted=True)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import StagingPurgeLogList1


async def finance_staging_purge_log_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = await request.app.state.dispatch_query_request(
    "urn:finance:staging_purge_log:list_purge_logs:1",
    {},
  )
  model = StagingPurgeLogList1(purge_logs=payload.get("rows") or [])
  return RPCResponse(op=rpc_request.op, payload=model.model_dump(), version=rpc_request.version)

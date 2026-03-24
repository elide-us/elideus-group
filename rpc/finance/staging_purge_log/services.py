from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import StagingPurgeLogList1


async def finance_staging_purge_log_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_purge_logs()
  model = StagingPurgeLogList1(purge_logs=[dict(row) for row in rows])
  return RPCResponse(op=rpc_request.op, payload=model.model_dump(), version=rpc_request.version)

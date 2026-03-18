from fastapi import Request

from queryregistry.finance.staging_purge_log import list_purge_logs_request
from queryregistry.finance.staging_purge_log.models import ListPurgeLogsParams
from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import StagingPurgeLogList1


async def finance_staging_purge_log_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_purge_logs_request(ListPurgeLogsParams()))
  model = StagingPurgeLogList1(purge_logs=result.rows or [])
  return RPCResponse(op=rpc_request.op, payload=model.model_dump(), version=rpc_request.version)

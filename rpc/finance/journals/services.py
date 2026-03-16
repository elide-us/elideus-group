from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  JournalCreate1,
  JournalGet1,
  JournalGetLines1,
  JournalItem1,
  JournalLineItem1,
  JournalLineList1,
  JournalList1,
  JournalListFilter1,
  JournalPost1,
  JournalReverse1,
)


def _coerce_line(line: dict) -> dict:
  coerced = dict(line)
  if "debit" in coerced:
    coerced["debit"] = str(coerced["debit"])
  if "credit" in coerced:
    coerced["credit"] = str(coerced["credit"])
  return coerced


async def finance_journals_list_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalListFilter1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.list_journals(status=input_payload.status, periods_guid=input_payload.periods_guid)
  payload = JournalList1(journals=[JournalItem1(**journal) for journal in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_journals_get_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalGet1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  row = await module.get_journal(input_payload.recid)
  if not row:
    raise HTTPException(status_code=404, detail="Journal not found")
  payload = JournalItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_journals_get_lines_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalGetLines1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  rows = await module.get_journal_lines(input_payload.journals_recid)
  payload = JournalLineList1(lines=[JournalLineItem1(**_coerce_line(line)) for line in rows])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_journals_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalCreate1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.create_journal(
      name=input_payload.name,
      description=input_payload.description,
      posting_key=input_payload.posting_key,
      source_type=input_payload.source_type,
      source_id=input_payload.source_id,
      periods_guid=input_payload.periods_guid,
      ledgers_recid=input_payload.ledgers_recid,
      lines=[line.model_dump() for line in input_payload.lines],
      post=input_payload.post,
      posted_by=auth_ctx.user_guid,
    )
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = JournalItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_journals_post_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalPost1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.post_journal(input_payload.recid, posted_by=auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = JournalItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def finance_journals_reverse_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  input_payload = JournalReverse1(**(rpc_request.payload or {}))
  module = request.app.state.finance
  await module.on_ready()
  try:
    row = await module.reverse_journal(input_payload.recid, posted_by=auth_ctx.user_guid)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = JournalItem1(**row)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

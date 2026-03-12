import logging

from fastapi import Request

from queryregistry.system.conversations import (
  delete_before_timestamp_request,
  delete_by_thread_request,
  get_stats_request,
  list_summary_request,
  list_thread_request,
)
from queryregistry.system.conversations.models import (
  ConversationStatsParams,
  DeleteByThreadParams,
  DeleteByTimestampParams,
  ListConversationSummaryParams,
  ListThreadParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  SystemConversationsConversationItem1,
  SystemConversationsDeleteBefore1,
  SystemConversationsDeleteResult1,
  SystemConversationsDeleteThread1,
  SystemConversationsList1,
  SystemConversationsStats1,
  SystemConversationsThread1,
  SystemConversationsThreadMessage1,
  SystemConversationsViewThread1,
)


async def system_conversations_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = rpc_request.payload or {}
  limit = int(payload.get("limit", 100))
  offset = int(payload.get("offset", 0))
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(list_summary_request(ListConversationSummaryParams(limit=limit, offset=offset)))
  conversations = []
  for row in res.rows or []:
    conversations.append(SystemConversationsConversationItem1(
      recid=row.get("recid", 0),
      personas_recid=row.get("personas_recid", 0),
      models_recid=row.get("models_recid", 0),
      guild_id=row.get("element_guild_id"),
      channel_id=row.get("element_channel_id"),
      user_id=row.get("element_user_id"),
      role=row.get("element_role"),
      thread_id=row.get("element_thread_id"),
      preview=row.get("element_preview", ""),
      tokens=row.get("element_tokens"),
      created_on=row.get("element_created_on"),
      persona_name=row.get("persona_name"),
    ))
  result = SystemConversationsList1(
    conversations=conversations,
    total=len(conversations),
    limit=limit,
    offset=offset,
  )
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_stats_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(get_stats_request(ConversationStatsParams()))
  row = res.rows[0] if res.rows else {}
  stats = SystemConversationsStats1(
    total_rows=int(row.get("total_rows", 0)),
    total_threads=int(row.get("total_threads", 0)),
    oldest_entry=row.get("oldest_entry"),
    newest_entry=row.get("newest_entry"),
    total_tokens=int(row.get("total_tokens", 0)),
  )
  return RPCResponse(op=rpc_request.op, payload=stats.model_dump(), version=rpc_request.version)


async def system_conversations_view_thread_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = SystemConversationsViewThread1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(list_thread_request(ListThreadParams(thread_id=payload.thread_id)))
  messages = []
  for row in res.rows or []:
    messages.append(SystemConversationsThreadMessage1(
      recid=row.get("recid", 0),
      role=row.get("element_role"),
      content=row.get("element_content"),
      user_id=row.get("element_user_id"),
      tokens=row.get("element_tokens"),
      created_on=row.get("element_created_on"),
    ))
  result = SystemConversationsThread1(thread_id=payload.thread_id, messages=messages)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_delete_thread_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = SystemConversationsDeleteThread1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(delete_by_thread_request(DeleteByThreadParams(thread_id=payload.thread_id)))
  logging.info(
    "[system_conversations_delete_thread_v1] deleted thread",
    extra={"user_guid": auth_ctx.user_guid, "thread_id": payload.thread_id, "rowcount": res.rowcount},
  )
  result = SystemConversationsDeleteResult1(deleted=res.rowcount)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_delete_before_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = SystemConversationsDeleteBefore1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(delete_before_timestamp_request(DeleteByTimestampParams(before=payload.before)))
  logging.info(
    "[system_conversations_delete_before_v1] deleted conversations before %s",
    payload.before,
    extra={"user_guid": auth_ctx.user_guid, "before": payload.before, "rowcount": res.rowcount},
  )
  result = SystemConversationsDeleteResult1(deleted=res.rowcount)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)

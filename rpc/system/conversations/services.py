import logging

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.conversations_module import ConversationsModule

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
  module: ConversationsModule = request.app.state.conversations
  await module.on_ready()
  rows = await module.list_conversations(limit=limit, offset=offset)
  conversations = [
    SystemConversationsConversationItem1(
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
    )
    for row in rows
  ]
  result = SystemConversationsList1(
    conversations=conversations,
    total=len(conversations),
    limit=limit,
    offset=offset,
  )
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_stats_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module: ConversationsModule = request.app.state.conversations
  await module.on_ready()
  row = await module.get_conversation_stats()
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
  module: ConversationsModule = request.app.state.conversations
  await module.on_ready()
  rows = await module.list_conversation_thread(payload.thread_id)
  messages = [
    SystemConversationsThreadMessage1(
      recid=row.get("recid", 0),
      role=row.get("element_role"),
      content=row.get("element_content"),
      user_id=row.get("element_user_id"),
      tokens=row.get("element_tokens"),
      created_on=row.get("element_created_on"),
    )
    for row in rows
  ]
  result = SystemConversationsThread1(thread_id=payload.thread_id, messages=messages)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_delete_thread_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = SystemConversationsDeleteThread1(**(rpc_request.payload or {}))
  module: ConversationsModule = request.app.state.conversations
  await module.on_ready()
  deleted = await module.delete_conversation_thread(payload.thread_id)
  logging.info(
    "[system_conversations_delete_thread_v1] deleted thread",
    extra={"user_guid": auth_ctx.user_guid, "thread_id": payload.thread_id, "rowcount": deleted},
  )
  result = SystemConversationsDeleteResult1(deleted=deleted)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def system_conversations_delete_before_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = SystemConversationsDeleteBefore1(**(rpc_request.payload or {}))
  module: ConversationsModule = request.app.state.conversations
  await module.on_ready()
  deleted = await module.delete_conversations_before(payload.before)
  logging.info(
    "[system_conversations_delete_before_v1] deleted conversations before %s",
    payload.before,
    extra={"user_guid": auth_ctx.user_guid, "before": payload.before, "rowcount": deleted},
  )
  result = SystemConversationsDeleteResult1(deleted=deleted)
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)

"""System conversations query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  ConversationStatsParams,
  DeleteByThreadParams,
  DeleteByTimestampParams,
  FindRecentParams,
  InsertConversationParams,
  InsertMessageParams,
  ListConversationSummaryParams,
  ListByTimeParams,
  ListChannelMessagesParams,
  ListThreadParams,
  UpdateOutputParams,
)

__all__ = [
  "find_recent_v1",
  "insert_conversation_v1",
  "insert_message_v1",
  "list_by_time_v1",
  "list_channel_messages_v1",
  "list_recent_v1",
  "list_summary_v1",
  "get_stats_v1",
  "delete_by_thread_v1",
  "delete_before_timestamp_v1",
  "list_thread_v1",
  "update_output_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_INSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.insert_conversation_v1}
_FIND_RECENT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.find_recent_v1}
_INSERT_MESSAGE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.insert_message_v1}
_UPDATE_OUTPUT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_output_v1}
_LIST_BY_TIME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_time_v1}
_LIST_THREAD_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_thread_v1}
_LIST_CHANNEL_MESSAGES_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_channel_messages_v1}
_LIST_RECENT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_recent_v1}
_LIST_SUMMARY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_summary_v1}
_GET_STATS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_stats_v1}
_DELETE_BY_THREAD_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_by_thread_v1}
_DELETE_BEFORE_TIMESTAMP_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_before_timestamp_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(
      f"Unsupported provider '{provider}' for system conversations registry"
    )
  return dispatcher


async def insert_conversation_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = InsertConversationParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _INSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def find_recent_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = FindRecentParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _FIND_RECENT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)




async def insert_message_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = InsertMessageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _INSERT_MESSAGE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

async def update_output_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateOutputParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_OUTPUT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_by_time_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListByTimeParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_BY_TIME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_recent_v1(request: DBRequest, *, provider: str) -> DBResponse:
  result = await _select_dispatcher(provider, _LIST_RECENT_DISPATCHERS)({})
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_thread_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListThreadParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_THREAD_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_channel_messages_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListChannelMessagesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_CHANNEL_MESSAGES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_summary_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListConversationSummaryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_SUMMARY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_stats_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ConversationStatsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_STATS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_by_thread_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteByThreadParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_BY_THREAD_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_before_timestamp_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteByTimestampParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_BEFORE_TIMESTAMP_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)

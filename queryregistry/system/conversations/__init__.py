"""System conversations query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

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
  "delete_before_timestamp_request",
  "delete_by_thread_request",
  "find_recent_request",
  "get_stats_request",
  "insert_conversation_request",
  "insert_message_request",
  "list_by_time_request",
  "list_channel_messages_request",
  "list_recent_request",
  "list_summary_request",
  "list_thread_request",
  "update_output_request",
]


def insert_conversation_request(params: InsertConversationParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:insert:1", payload=params.model_dump())


def find_recent_request(params: FindRecentParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:find_recent:1", payload=params.model_dump())


def insert_message_request(params: InsertMessageParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:insert_message:1", payload=params.model_dump())


def update_output_request(params: UpdateOutputParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:update_output:1", payload=params.model_dump())


def list_by_time_request(params: ListByTimeParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:list_by_time:1", payload=params.model_dump())


def list_recent_request() -> DBRequest:
  return DBRequest(op="db:system:conversations:list_recent:1", payload={})


def list_thread_request(params: ListThreadParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:list_thread:1", payload=params.model_dump())


def list_channel_messages_request(params: ListChannelMessagesParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:list_channel_messages:1", payload=params.model_dump())


def list_summary_request(params: ListConversationSummaryParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:list_summary:1", payload=params.model_dump())


def get_stats_request(params: ConversationStatsParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:get_stats:1", payload=params.model_dump())


def delete_by_thread_request(params: DeleteByThreadParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:delete_by_thread:1", payload=params.model_dump())


def delete_before_timestamp_request(params: DeleteByTimestampParams) -> DBRequest:
  return DBRequest(op="db:system:conversations:delete_before_timestamp:1", payload=params.model_dump())

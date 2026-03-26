"""System conversations domain module."""

from typing import Any

from fastapi import FastAPI

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

from . import BaseModule
from .db_module import DbModule


class ConversationsModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.conversations = self
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_conversations(self, limit: int, offset: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_summary_request(ListConversationSummaryParams(limit=limit, offset=offset)))
    return list(res.rows or [])

  async def get_conversation_stats(self) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(get_stats_request(ConversationStatsParams()))
    return dict(res.rows[0]) if res.rows else {}

  async def list_conversation_thread(self, thread_id: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_thread_request(ListThreadParams(thread_id=thread_id)))
    return list(res.rows or [])

  async def delete_conversation_thread(self, thread_id: str) -> int:
    assert self.db
    res = await self.db.run(delete_by_thread_request(DeleteByThreadParams(thread_id=thread_id)))
    return res.rowcount

  async def delete_conversations_before(self, before: str) -> int:
    assert self.db
    res = await self.db.run(delete_before_timestamp_request(DeleteByTimestampParams(before=before)))
    return res.rowcount

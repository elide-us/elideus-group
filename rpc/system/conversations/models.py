from typing import Optional

from pydantic import BaseModel


class SystemConversationsConversationItem1(BaseModel):
  recid: int
  personas_recid: int = 0
  models_recid: int = 0
  guild_id: Optional[str] = None
  channel_id: Optional[str] = None
  user_id: Optional[str] = None
  role: Optional[str] = None
  thread_id: Optional[str] = None
  preview: str = ""
  tokens: Optional[int] = None
  created_on: Optional[str] = None
  persona_name: Optional[str] = None


class SystemConversationsList1(BaseModel):
  conversations: list[SystemConversationsConversationItem1]
  total: int = 0
  limit: int = 100
  offset: int = 0


class SystemConversationsStats1(BaseModel):
  total_rows: int = 0
  total_threads: int = 0
  oldest_entry: Optional[str] = None
  newest_entry: Optional[str] = None
  total_tokens: int = 0


class SystemConversationsThreadMessage1(BaseModel):
  recid: int
  role: Optional[str] = None
  content: Optional[str] = None
  user_id: Optional[str] = None
  tokens: Optional[int] = None
  created_on: Optional[str] = None


class SystemConversationsThread1(BaseModel):
  thread_id: str
  messages: list[SystemConversationsThreadMessage1]


class SystemConversationsViewThread1(BaseModel):
  thread_id: str


class SystemConversationsDeleteThread1(BaseModel):
  thread_id: str


class SystemConversationsDeleteBefore1(BaseModel):
  before: str


class SystemConversationsDeleteResult1(BaseModel):
  deleted: int = 0

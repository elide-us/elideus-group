from pydantic import BaseModel
from typing import List, Optional


class DiscordChatSummarizeChannelRequest1(BaseModel):
  channel_id: str


class DiscordChatSummarizeChannelResponse1(BaseModel):
  summary: str


class DiscordChatUwuChatRequest1(BaseModel):
  message: str
  guild_id: int
  channel_id: int
  user_id: int


class DiscordChatUwuChatResponse1(BaseModel):
  uwu_response_text: str
  summary_lines: List[str] = []
  token_count_estimate: Optional[int] = None

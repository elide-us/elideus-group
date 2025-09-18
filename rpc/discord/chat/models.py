from pydantic import BaseModel
from typing import List, Optional


class DiscordChatSummarizeChannelRequest1(BaseModel):
  channel_id: str


class DiscordChatSummarizeChannelResponse1(BaseModel):
  summary: str
  messages_collected: int | None = None
  token_count_estimate: int | None = None
  cap_hit: bool | None = None
  model: str | None = None
  role: str | None = None


class DiscordChatPersonaRequest1(BaseModel):
  persona: str
  message: str
  guild_id: Optional[int] = None
  channel_id: Optional[int] = None
  user_id: Optional[int] = None


class DiscordChatPersonaResponse1(BaseModel):
  persona: str
  persona_response_text: str
  model: Optional[str] = None
  role: Optional[str] = None

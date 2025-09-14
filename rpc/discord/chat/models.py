from pydantic import BaseModel


class DiscordChatSummarizeChannelRequest1(BaseModel):
  channel_id: str


class DiscordChatSummarizeChannelResponse1(BaseModel):
  summary: str


class DiscordChatUwuChatRequest1(BaseModel):
  message: str


class DiscordChatUwuChatResponse1(BaseModel):
  message: str

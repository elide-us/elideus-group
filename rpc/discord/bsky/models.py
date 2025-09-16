from pydantic import BaseModel


class DiscordBskyPostRequest1(BaseModel):
  message: str


class DiscordBskyPostResponse1(BaseModel):
  uri: str
  cid: str
  handle: str
  display_name: str | None = None

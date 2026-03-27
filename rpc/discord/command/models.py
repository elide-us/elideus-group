from pydantic import BaseModel


class DiscordCommandGetCreditsRequest1(BaseModel):
  discord_id: str


class DiscordCommandGetCreditsResponse1(BaseModel):
  credits: int
  reserve: int | None = None


class DiscordCommandGetGuildCreditsRequest1(BaseModel):
  guild_id: str


class DiscordCommandGetGuildCreditsResponse1(BaseModel):
  guild_id: str
  credits: int

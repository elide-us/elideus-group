from pydantic import BaseModel


class DiscordGuildsGuildItem1(BaseModel):
  recid: int
  guild_id: str
  name: str
  joined_on: str | None = None
  member_count: int | None = None
  owner_id: str | None = None
  region: str | None = None
  left_on: str | None = None
  notes: str | None = None
  credits: int = 0


class DiscordGuildsList1(BaseModel):
  guilds: list[DiscordGuildsGuildItem1]


class DiscordGuildsUpdateCredits1(BaseModel):
  guild_id: str
  credits: int


class DiscordGuildsSyncResult1(BaseModel):
  synced: int
  guilds: list[DiscordGuildsGuildItem1]

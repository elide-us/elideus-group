from pydantic import BaseModel


class DiscordCommandTextUwuResponse1(BaseModel):
  message: str


class DiscordCommandGetRolesResponse1(BaseModel):
  roles: list[str]


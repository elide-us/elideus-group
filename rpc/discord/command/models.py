from pydantic import BaseModel


class DiscordCommandGetRolesResponse1(BaseModel):
  roles: list[str]


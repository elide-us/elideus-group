from pydantic import BaseModel


class DiscordOngoingToggleActiveResponse1(BaseModel):
  active: bool


class DiscordOngoingCountdownResponse1(BaseModel):
  active: bool
  seconds_remaining: float | None

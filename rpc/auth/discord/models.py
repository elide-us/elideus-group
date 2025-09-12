from typing import Optional

from pydantic import BaseModel


class AuthDiscordOauthLoginPayload1(BaseModel):
  provider: str = "discord"
  code: str
  fingerprint: str
  confirm: bool | None = None
  reauthToken: str | None = None


class AuthDiscordOauthLogin1(BaseModel):
  sessionToken: str
  display_name: str
  credits: int
  profile_image: Optional[str] = None

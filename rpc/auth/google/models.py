from typing import Optional

from pydantic import BaseModel


class AuthGoogleOauthLoginPayload1(BaseModel):
  provider: str = "google"
  code: str
  confirm: bool | None = None
  reauthToken: str | None = None
  fingerprint: str


class AuthGoogleOauthLogin1(BaseModel):
  sessionToken: str
  display_name: str
  credits: int
  profile_image: Optional[str] = None

from typing import Optional

from pydantic import BaseModel


class AuthMicrosoftOauthLoginPayload1(BaseModel):
  provider: str = "microsoft"
  idToken: str | None = None
  id_token: str | None = None
  accessToken: str | None = None
  access_token: str | None = None
  fingerprint: str
  confirm: bool | None = None
  reAuthToken: str | None = None


class AuthMicrosoftOauthLogin1(BaseModel):
  sessionToken: str
  display_name: str
  credits: int
  profile_image: Optional[str] = None

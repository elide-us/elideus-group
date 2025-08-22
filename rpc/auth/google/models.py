from typing import Optional

from pydantic import BaseModel


class AuthGoogleOauthLoginPayload1(BaseModel):
  provider: str = "google"
  code: str
  code_verifier: str | None = None
  fingerprint: str | None = None


class AuthGoogleOauthLogin1(BaseModel):
  sessionToken: str
  display_name: str
  credits: int
  profile_image: Optional[str] = None

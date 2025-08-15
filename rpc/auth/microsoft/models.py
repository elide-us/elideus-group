from typing import Optional

from pydantic import BaseModel


class AuthMicrosoftOauthLogin1(BaseModel):
  sessionToken: str
  display_name: str
  credits: int
  profile_image: Optional[str] = None

from typing import List, Optional

from pydantic import BaseModel


class UsersProfileAuthProvider1(BaseModel):
  name: str
  display: str


class UsersProfileProfile1(BaseModel):
  guid: str
  display_name: str
  email: str
  display_email: bool
  credits: int
  profile_image: Optional[str] = None
  auth_providers: List[UsersProfileAuthProvider1] = []


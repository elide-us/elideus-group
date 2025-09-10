from typing import Optional
from pydantic import BaseModel

class PublicUsersProfile1(BaseModel):
  display_name: str
  email: Optional[str] = None
  profile_image: Optional[str] = None

class PublicUsersPublishedFile1(BaseModel):
  path: str
  filename: str

class PublicUsersPublishedFiles1(BaseModel):
  files: list[PublicUsersPublishedFile1]

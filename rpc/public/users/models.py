from typing import Optional
from pydantic import BaseModel


class PublicUsersGetProfileRequest1(BaseModel):
  guid: str


class PublicUsersGetPublishedFilesRequest1(BaseModel):
  guid: str


class PublicUsersProfile1(BaseModel):
  display_name: str
  email: Optional[str] = None
  profile_image: Optional[str] = None


class PublicUsersPublishedFile1(BaseModel):
  path: str
  filename: str
  url: str
  content_type: Optional[str] = None


class PublicUsersPublishedFiles1(BaseModel):
  files: list[PublicUsersPublishedFile1]

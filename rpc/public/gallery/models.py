from typing import Optional
from pydantic import BaseModel

class PublicGalleryFileItem1(BaseModel):
  path: str
  name: str
  url: str
  content_type: Optional[str] = None
  user_guid: Optional[str] = None
  display_name: Optional[str] = None

class PublicGalleryFiles1(BaseModel):
  files: list[PublicGalleryFileItem1]

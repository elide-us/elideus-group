from pydantic import BaseModel
from typing import Optional

class FileItem(BaseModel):
  name: str
  url: str
  contentType: Optional[str] = None

class FrontendFilesList1(BaseModel):
  files: list[FileItem]

class FrontendFileDelete1(BaseModel):
  bearerToken: str
  filename: str

class FrontendFileUpload1(BaseModel):
  bearerToken: str
  filename: str
  dataUrl: str
  contentType: str

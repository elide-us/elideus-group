from typing import Optional

from pydantic import BaseModel


class FileItem(BaseModel):
  name: str
  url: str
  contentType: Optional[str] = None

class StorageFilesList1(BaseModel):
  files: list[FileItem]

class StorageFileDelete1(BaseModel):
  bearerToken: str
  filename: str

class StorageFileUpload1(BaseModel):
  bearerToken: str
  filename: str
  dataUrl: str
  contentType: str

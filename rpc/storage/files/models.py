from typing import Optional

from pydantic import BaseModel

class StorageFilesItem1(BaseModel):
  name: str
  url: str
  contentType: Optional[str] = None

class StorageFilesItemList1(BaseModel):
  files: list[StorageFilesItem1]

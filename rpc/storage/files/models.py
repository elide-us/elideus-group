from typing import List, Optional

from pydantic import BaseModel


class StorageFilesFileItem1(BaseModel):
  name: str
  url: str
  content_type: Optional[str] = None


class StorageFilesFiles1(BaseModel):
  files: List[StorageFilesFileItem1]


class StorageFilesUploadFile1(BaseModel):
  name: str
  content_b64: str
  content_type: Optional[str] = None


class StorageFilesUploadFiles1(BaseModel):
  files: List[StorageFilesUploadFile1]


class StorageFilesDeleteFiles1(BaseModel):
  files: List[str]


class StorageFilesSetGallery1(BaseModel):
  name: str
  gallery: bool


class StorageFilesCreateFolder1(BaseModel):
  path: str


class StorageFilesMoveFile1(BaseModel):
  src: str
  dst: str

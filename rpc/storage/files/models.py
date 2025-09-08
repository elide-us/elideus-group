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


class StorageFilesGetLink1(BaseModel):
  name: str


class StorageFilesGetFolderFiles1(BaseModel):
  path: str


class StorageFilesFolderItem1(BaseModel):
  name: str
  empty: bool


class StorageFilesFolderListing1(BaseModel):
  path: str
  files: List[StorageFilesFileItem1]
  folders: List[StorageFilesFolderItem1]


class StorageFilesDeleteFolder1(BaseModel):
  path: str


class StorageFilesCreateUserFolder1(BaseModel):
  path: str


class StorageFilesRenameFile1(BaseModel):
  old_name: str
  new_name: str


class StorageFilesGetMetadata1(BaseModel):
  name: str


class StorageFilesFileMetadata1(BaseModel):
  name: str
  size: int
  content_type: Optional[str] = None
  created_on: str
  modified_on: str


class StorageFilesUsageItem1(BaseModel):
  content_type: str
  size: int


class StorageFilesUsage1(BaseModel):
  total_size: int
  by_type: List[StorageFilesUsageItem1]

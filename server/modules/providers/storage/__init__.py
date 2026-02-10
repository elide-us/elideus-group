"""Storage provider interfaces and shared data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from .. import LifecycleProvider



@dataclass(slots=True)
class StorageBlobItem:
  """Representation of a blob returned from storage."""

  name: str
  metadata: dict[str, Any]
  content_type: str | None
  created_on: datetime | None
  modified_on: datetime | None
  url: str
  size: int | None
  is_directory: bool


@dataclass(slots=True)
class StorageReindexRequest:
  container_name: str
  prefix: str | None = None


@dataclass(slots=True)
class StorageReindexResponse:
  container_url: str
  blobs: list[StorageBlobItem]


@dataclass(slots=True)
class StorageUploadFile:
  blob_name: str
  relative_path: str
  data: bytes
  content_type: str | None


@dataclass(slots=True)
class StorageUploadRequest:
  container_name: str
  files: Sequence[StorageUploadFile]


@dataclass(slots=True)
class StorageUploadResult:
  relative_path: str
  url: str
  content_type: str | None
  created_on: datetime
  modified_on: datetime


@dataclass(slots=True)
class StorageUploadResponse:
  results: list[StorageUploadResult]
  errors: dict[str, str]


@dataclass(slots=True)
class StorageDeleteRequest:
  container_name: str
  blob_names: Sequence[str]
  relative_paths: Sequence[str]


@dataclass(slots=True)
class StorageDeleteResponse:
  deleted: list[str]
  errors: dict[str, str]


@dataclass(slots=True)
class StorageDeletedEntry:
  relative_path: str


@dataclass(slots=True)
class StorageDeleteFolderRequest:
  container_name: str
  user_guid: str
  prefix: str


@dataclass(slots=True)
class StorageDeleteFolderResponse:
  deleted_entries: list[StorageDeletedEntry]
  errors: dict[str, str]


@dataclass(slots=True)
class StorageCreateFolderRequest:
  container_name: str
  blob_name: str
  init_blob_name: str


@dataclass(slots=True)
class StorageCreateFolderResult:
  relative_path: str


@dataclass(slots=True)
class StorageMoveRequest:
  container_name: str
  src_blob: str
  dst_blob: str
  src_relative: str
  dst_relative: str


@dataclass(slots=True)
class StorageBlobProperties:
  content_type: str | None
  created_on: datetime | None
  modified_on: datetime | None


@dataclass(slots=True)
class StorageMoveResult:
  src_relative: str
  dst_relative: str
  url: str | None
  properties: StorageBlobProperties


@dataclass(slots=True)
class StorageRenameRequest:
  container_name: str
  user_guid: str
  old_relative: str
  new_relative: str
  is_folder: bool


@dataclass(slots=True)
class StorageRenameOperation:
  old_relative: str
  new_relative: str
  url: str | None
  properties: StorageBlobProperties | None
  source_missing: bool


@dataclass(slots=True)
class StorageRenameResponse:
  container_url: str
  operations: list[StorageRenameOperation]
  errors: list[str]


@dataclass(slots=True)
class StorageStatsRequest:
  container_name: str


@dataclass(slots=True)
class StorageStats:
  file_count: int
  total_bytes: int
  folder_paths: list[tuple[str, str]]
  user_ids: list[str]


class StorageProvider(LifecycleProvider):
  """Base class for storage providers."""

  async def startup(self) -> None:  # pragma: no cover - interface default
    return None

  async def shutdown(self) -> None:  # pragma: no cover - interface default
    return None

  async def reindex(self, request: StorageReindexRequest) -> StorageReindexResponse:
    raise NotImplementedError

  async def upload_files(self, request: StorageUploadRequest) -> StorageUploadResponse:
    raise NotImplementedError

  async def delete_files(self, request: StorageDeleteRequest) -> StorageDeleteResponse:
    raise NotImplementedError

  async def delete_folder(self, request: StorageDeleteFolderRequest) -> StorageDeleteFolderResponse:
    raise NotImplementedError

  async def create_folder(self, request: StorageCreateFolderRequest) -> StorageCreateFolderResult:
    raise NotImplementedError

  async def move_file(self, request: StorageMoveRequest) -> StorageMoveResult | None:
    raise NotImplementedError

  async def rename_file(self, request: StorageRenameRequest) -> StorageRenameResponse:
    raise NotImplementedError

  async def get_storage_stats(self, request: StorageStatsRequest) -> StorageStats:
    raise NotImplementedError

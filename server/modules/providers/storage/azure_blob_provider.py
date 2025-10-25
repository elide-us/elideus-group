"""Azure Blob Storage provider implementation."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings

from . import (
  StorageBlobItem,
  StorageBlobProperties,
  StorageCreateFolderRequest,
  StorageCreateFolderResult,
  StorageDeleteFolderRequest,
  StorageDeleteFolderResponse,
  StorageDeleteRequest,
  StorageDeleteResponse,
  StorageDeletedEntry,
  StorageMoveRequest,
  StorageMoveResult,
  StorageProvider,
  StorageReindexRequest,
  StorageReindexResponse,
  StorageRenameOperation,
  StorageRenameRequest,
  StorageRenameResponse,
  StorageStats,
  StorageStatsRequest,
  StorageUploadFile,
  StorageUploadRequest,
  StorageUploadResponse,
  StorageUploadResult,
)


class AzureBlobStorageProvider(StorageProvider):
  """Provider encapsulating Azure Blob interactions."""

  def __init__(self, *, connection_string: str):
    super().__init__()
    self.connection_string = connection_string

  async def startup(self) -> None:
    if not self.connection_string:
      logging.error("[AzureBlobStorageProvider] Missing connection string")

  async def shutdown(self) -> None:
    return None

  async def _open_container(self, container_name: str):
    if not self.connection_string:
      raise ValueError("Azure connection string is not configured")
    if not container_name:
      raise ValueError("Azure container name is required")
    service = BlobServiceClient.from_connection_string(self.connection_string)
    container = service.get_container_client(container_name)
    return service, container

  def _extract_properties(self, blob: Any, *, container_url: str) -> StorageBlobItem:
    metadata = getattr(blob, "metadata", {}) or {}
    content_type = None
    if hasattr(blob, "content_settings") and blob.content_settings:
      content_type = getattr(blob.content_settings, "content_type", None)
    if not content_type:
      content_type = getattr(blob, "content_type", None)
    created_on = getattr(blob, "creation_time", None) or getattr(blob, "created_on", None)
    modified_on = getattr(blob, "last_modified", None)
    size = getattr(blob, "size", None)
    if size is None:
      props = getattr(blob, "properties", None)
      if props is not None:
        size = getattr(props, "content_length", None)
    name = getattr(blob, "name", "")
    return StorageBlobItem(
      name=name,
      metadata=dict(metadata),
      content_type=content_type,
      created_on=created_on,
      modified_on=modified_on,
      url=f"{container_url}/{name}" if name else "",
      size=size,
      is_directory=metadata.get("hdi_isfolder") == "true",
    )

  async def reindex(self, request: StorageReindexRequest) -> StorageReindexResponse:
    service, container = await self._open_container(request.container_name)
    container_url = container.url
    blobs: list[StorageBlobItem] = []
    try:
      iterator = (
        container.list_blobs(name_starts_with=request.prefix)
        if request.prefix
        else container.list_blobs()
      )
      async for blob in iterator:
        item = self._extract_properties(blob, container_url=container_url)
        if not item.name:
          continue
        blobs.append(item)
    finally:
      await container.close()
      await service.close()
    return StorageReindexResponse(container_url=container_url, blobs=blobs)

  async def upload_files(self, request: StorageUploadRequest) -> StorageUploadResponse:
    service, container = await self._open_container(request.container_name)
    container_url = container.url
    results: list[StorageUploadResult] = []
    errors: dict[str, str] = {}
    try:
      now = datetime.now(timezone.utc)
      for file in request.files:
        try:
          await container.upload_blob(
            file.blob_name,
            file.data,
            overwrite=True,
            content_settings=ContentSettings(content_type=file.content_type) if file.content_type else None,
          )
        except Exception as exc:  # pragma: no cover - network failure
          logging.error("[AzureBlobStorageProvider] Failed to upload %s: %s", file.blob_name, exc)
          errors[file.relative_path] = str(exc)
          continue
        results.append(
          StorageUploadResult(
            relative_path=file.relative_path,
            url=f"{container_url}/{file.blob_name}",
            content_type=file.content_type,
            created_on=now,
            modified_on=now,
          )
        )
    finally:
      await container.close()
      await service.close()
    return StorageUploadResponse(results=results, errors=errors)

  async def delete_files(self, request: StorageDeleteRequest) -> StorageDeleteResponse:
    service, container = await self._open_container(request.container_name)
    deleted: list[str] = []
    errors: dict[str, str] = {}
    try:
      for blob_name, rel in zip(request.blob_names, request.relative_paths):
        blob = container.get_blob_client(blob_name)
        try:
          await blob.delete_blob()
          deleted.append(rel)
        except Exception as exc:  # pragma: no cover - network failure
          logging.error("[AzureBlobStorageProvider] Failed to delete %s: %s", blob_name, exc)
          errors[rel] = str(exc)
    finally:
      await container.close()
      await service.close()
    return StorageDeleteResponse(deleted=deleted, errors=errors)

  async def delete_folder(self, request: StorageDeleteFolderRequest) -> StorageDeleteFolderResponse:
    service, container = await self._open_container(request.container_name)
    deleted_entries: list[StorageDeletedEntry] = []
    errors: dict[str, str] = {}
    try:
      async for blob in container.list_blobs(name_starts_with=request.prefix):
        name = getattr(blob, "name", None)
        if not name or not name.startswith(f"{request.user_guid}/"):
          continue
        try:
          await container.delete_blob(name)
          relative = name[len(f"{request.user_guid}/"):]
          deleted_entries.append(StorageDeletedEntry(relative_path=relative))
        except Exception as exc:  # pragma: no cover - network failure
          logging.error("[AzureBlobStorageProvider] Failed to delete %s: %s", name, exc)
          errors[name] = str(exc)
    finally:
      await container.close()
      await service.close()
    return StorageDeleteFolderResponse(deleted_entries=deleted_entries, errors=errors)

  async def create_folder(self, request: StorageCreateFolderRequest) -> StorageCreateFolderResult:
    service, container = await self._open_container(request.container_name)
    try:
      await container.upload_blob(
        request.blob_name,
        b"",
        metadata={"hdi_isfolder": "true"},
        overwrite=True,
      )
      await container.upload_blob(
        request.init_blob_name,
        b"",
        overwrite=True,
      )
      rel = request.blob_name.split("/", 1)[-1]
      return StorageCreateFolderResult(relative_path=rel)
    finally:
      await container.close()
      await service.close()

  async def move_file(self, request: StorageMoveRequest) -> StorageMoveResult | None:
    service, container = await self._open_container(request.container_name)
    try:
      src_blob = container.get_blob_client(request.src_blob)
      dst_blob = container.get_blob_client(request.dst_blob)
      props = await src_blob.get_blob_properties()
      await dst_blob.start_copy_from_url(src_blob.url)
      await src_blob.delete_blob()
      ct = None
      if getattr(props, "content_settings", None):
        ct = getattr(props.content_settings, "content_type", None)
      created_on = getattr(props, "creation_time", None) or getattr(props, "created_on", None)
      modified_on = getattr(props, "last_modified", None)
      properties = StorageBlobProperties(
        content_type=ct or "application/octet-stream",
        created_on=created_on,
        modified_on=modified_on,
      )
      return StorageMoveResult(
        src_relative=request.src_relative,
        dst_relative=request.dst_relative,
        url=dst_blob.url,
        properties=properties,
      )
    except Exception as exc:  # pragma: no cover - network failure
      logging.error(
        "[AzureBlobStorageProvider] Failed to move blob %s -> %s: %s",
        request.src_blob,
        request.dst_blob,
        exc,
      )
      return None
    finally:
      await container.close()
      await service.close()

  async def rename_file(self, request: StorageRenameRequest) -> StorageRenameResponse:
    service, container = await self._open_container(request.container_name)
    container_url = container.url
    operations: list[StorageRenameOperation] = []
    errors: list[str] = []

    def _full_name(relative: str) -> str:
      if relative.startswith(f"{request.user_guid}/"):
        return relative
      return f"{request.user_guid}/{relative.lstrip('/')}"  # type: ignore[no-any-return]

    async def rename_single(old_rel: str, new_rel: str) -> None:
      src_name = _full_name(old_rel)
      dst_name = _full_name(new_rel)
      src_blob = container.get_blob_client(src_name)
      dst_blob = container.get_blob_client(dst_name)
      try:
        src_exists = await src_blob.exists()
      except Exception as exc:  # pragma: no cover - network failure
        logging.error("[AzureBlobStorageProvider] Failed to check blob %s: %s", src_name, exc)
        errors.append(f"exists:{src_name}:{exc}")
        return
      if not src_exists:
        operations.append(
          StorageRenameOperation(
            old_relative=old_rel,
            new_relative=new_rel,
            url=None,
            properties=None,
            source_missing=True,
          )
        )
        return
      try:
        if await dst_blob.exists():
          msg = f"Destination blob already exists for rename {old_rel} -> {new_rel}"
          logging.error("[AzureBlobStorageProvider] %s", msg)
          errors.append(f"exists:{dst_name}")
          return
      except Exception as exc:  # pragma: no cover - network failure
        logging.error("[AzureBlobStorageProvider] Failed to check destination blob %s: %s", dst_name, exc)
        errors.append(f"dst-check:{dst_name}:{exc}")
        return
      try:
        props = await src_blob.get_blob_properties()
        await dst_blob.start_copy_from_url(src_blob.url)
        await src_blob.delete_blob()
        ct = None
        if getattr(props, "content_settings", None):
          ct = getattr(props.content_settings, "content_type", None)
        created_on = getattr(props, "creation_time", None) or getattr(props, "created_on", None)
        modified_on = getattr(props, "last_modified", None)
        properties = StorageBlobProperties(
          content_type=ct or "application/octet-stream",
          created_on=created_on,
          modified_on=modified_on,
        )
        operations.append(
          StorageRenameOperation(
            old_relative=old_rel,
            new_relative=new_rel,
            url=dst_blob.url,
            properties=properties,
            source_missing=False,
          )
        )
      except Exception as exc:  # pragma: no cover - network failure
        logging.error(
          "[AzureBlobStorageProvider] Failed to rename blob %s to %s: %s",
          old_rel,
          new_rel,
          exc,
        )
        errors.append(f"rename:{old_rel}:{new_rel}:{exc}")

    async def rename_folder(old_rel: str, new_rel: str) -> None:
      if new_rel.startswith(f"{old_rel}/"):
        msg = f"Cannot rename folder {old_rel} into its own child {new_rel}"
        logging.error("[AzureBlobStorageProvider] %s", msg)
        errors.append(f"cycle:{old_rel}->{new_rel}")
        return
      src_prefix = _full_name(old_rel)
      dst_prefix = _full_name(new_rel)
      dst_placeholder = container.get_blob_client(dst_prefix)
      try:
        if await dst_placeholder.exists():
          msg = f"Target folder {new_rel} already exists"
          logging.error("[AzureBlobStorageProvider] %s", msg)
          errors.append(f"exists:{dst_prefix}")
          return
      except Exception as exc:  # pragma: no cover - network failure
        logging.error("[AzureBlobStorageProvider] Failed to check destination folder %s: %s", dst_prefix, exc)
        errors.append(f"dst-check:{dst_prefix}:{exc}")
        return
      try:
        async for _ in container.list_blobs(name_starts_with=f"{dst_prefix}/"):
          msg = f"Target folder {new_rel} already contains blobs"
          logging.error("[AzureBlobStorageProvider] %s", msg)
          errors.append(f"nonempty:{dst_prefix}")
          return
      except Exception as exc:  # pragma: no cover - network failure
        logging.error("[AzureBlobStorageProvider] Failed to inspect destination folder %s: %s", dst_prefix, exc)
        errors.append(f"inspect:{dst_prefix}:{exc}")
        return
      await rename_single(old_rel, new_rel)
      try:
        async for blob in container.list_blobs(name_starts_with=f"{src_prefix}/"):
          rel_name = blob.name[len(f"{request.user_guid}/"):]
          if not rel_name:
            continue
          suffix = rel_name[len(old_rel):]
          await rename_single(rel_name, f"{new_rel}{suffix}")
      except Exception as exc:  # pragma: no cover - network failure
        logging.error("[AzureBlobStorageProvider] Failed to list blobs for folder %s: %s", old_rel, exc)
        errors.append(f"list:{src_prefix}:{exc}")

    try:
      if request.is_folder:
        await rename_folder(request.old_relative, request.new_relative)
      else:
        await rename_single(request.old_relative, request.new_relative)
    finally:
      await container.close()
      await service.close()
    return StorageRenameResponse(
      container_url=container_url,
      operations=operations,
      errors=errors,
    )

  async def get_storage_stats(self, request: StorageStatsRequest) -> StorageStats:
    service, container = await self._open_container(request.container_name)
    file_count = 0
    total_bytes = 0
    folders: set[tuple[str, str]] = set()
    users: set[str] = set()
    try:
      async for blob in container.list_blobs():
        name = getattr(blob, "name", "")
        if not name:
          continue
        parts = name.split("/")
        if len(parts) < 2:
          continue
        guid = parts[0]
        try:
          UUID(guid)
        except Exception:
          continue
        users.add(guid)
        parent = ""
        for folder_name in parts[1:-1]:
          parent = f"{parent}/{folder_name}" if parent else folder_name
          folders.add((guid, parent))
        if parts[-1] == ".init":
          continue
        file_count += 1
        size = getattr(blob, "size", None)
        if size is None:
          props = getattr(blob, "properties", None)
          if props is not None:
            size = getattr(props, "content_length", 0)
        total_bytes += size or 0
    finally:
      await container.close()
      await service.close()
    return StorageStats(
      file_count=file_count,
      total_bytes=total_bytes,
      folder_paths=sorted(folders),
      user_ids=sorted(users),
    )

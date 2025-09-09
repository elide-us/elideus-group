"""Storage management module for indexing Azure Blob contents."""

import asyncio, logging, re
from uuid import UUID
from azure.storage.blob.aio import BlobServiceClient
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule


class StorageModule(BaseModule):
  """Module responsible for cataloging files stored in Azure Blob Storage.

  The module maintains a background task that periodically triggers a
  reindex operation. Database helpers are provided for upserting file
  metadata and querying indexed data.
  """

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.env: EnvModule | None = None
    self.db: DbModule | None = None
    self.connection_string: str | None = None
    self._reindex_task: asyncio.Task | None = None
    self.reindex_interval = 15 * 60

  @staticmethod
  def _parse_duration(value: str) -> int:
    match = re.fullmatch(r"(\d+)([smhdw])", value.strip().lower())
    if not match:
      raise ValueError(f"Invalid duration: {value}")
    num, unit = match.groups()
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(num) * mult[unit]

  async def startup(self):
    self.env = self.app.state.env
    await self.env.on_ready()
    self.db = self.app.state.db
    await self.db.on_ready()
    try:
      self.connection_string = self.env.get("AZURE_BLOB_CONNECTION_STRING")
      if not self.connection_string:
        logging.error("[StorageModule] AZURE_BLOB_CONNECTION_STRING missing")
    except Exception as e:
      logging.error("[StorageModule] Failed to load AZURE_BLOB_CONNECTION_STRING: %s", e)

    try:
      res = await self.db.run("db:system:config:get_config:1", {"key": "StorageCacheTime"})
      value = res.rows[0]["value"] if res.rows else "15m"
      try:
        self.reindex_interval = self._parse_duration(value)
      except Exception:
        logging.error("[StorageModule] Invalid StorageCacheTime '%s'", value)
    except Exception as e:
      logging.error("[StorageModule] Failed to load StorageCacheTime: %s", e)
    self._reindex_task = asyncio.create_task(self._reindex_loop())
    logging.info("Storage module loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._reindex_task:
      self._reindex_task.cancel()
      try:
        await self._reindex_task
      except asyncio.CancelledError:
        pass
      self._reindex_task = None

  async def _reindex_loop(self):
    while True:
      await asyncio.sleep(self.reindex_interval)
      try:
        await self.reindex()
      except Exception as e:
        logging.error("[StorageModule] Reindex failed: %s", e)

  async def reindex(self, user_guid: str | None = None):
    """Perform a scan of storage and update database cache."""
    if not self.connection_string or not self.db:
      logging.error("[StorageModule] Missing connection string or database module")
      return
    res = await self.db.run("db:system:config:get_config:1", {"key": "AzureBlobContainerName"})
    container_name = res.rows[0]["value"] if res.rows else None
    if not container_name:
      logging.error("[StorageModule] AzureBlobContainerName missing")
      return
    bsc = BlobServiceClient.from_connection_string(self.connection_string)
    container = bsc.get_container_client(container_name)
    seen: dict[str, set[tuple[str, str]]] = {}
    folder_seen: dict[str, set[tuple[str, str]]] = {}
    prefix = f"{user_guid}/" if user_guid else None
    try:
      iterator = container.list_blobs(name_starts_with=prefix) if prefix else container.list_blobs()
      async for blob in iterator:
        name = getattr(blob, "name", None)
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
        if user_guid and guid != user_guid:
          continue
        filename = parts[-1]
        if filename == ".init":
          continue
        path = "/".join(parts[1:-1])
        # index folders along the path
        parent = ""
        fset = folder_seen.setdefault(guid, set())
        for folder_name in parts[1:-1]:
          key = (parent, folder_name)
          if key not in fset:
            await self.db.upsert_storage_cache({
              "user_guid": guid,
              "path": parent,
              "filename": folder_name,
              "content_type": "path/folder",
              "public": 0,
              "created_on": None,
              "modified_on": None,
              "url": None,
              "reported": 0,
              "moderation_recid": None,
            })
            fset.add(key)
          seen.setdefault(guid, set()).add(key)
          parent = f"{parent}/{folder_name}" if parent else folder_name
        ct = None
        if hasattr(blob, "content_settings") and blob.content_settings:
          ct = getattr(blob.content_settings, "content_type", None)
        if not ct:
          ct = getattr(blob, "content_type", None)
        created_on = getattr(blob, "creation_time", None) or getattr(blob, "created_on", None)
        modified_on = getattr(blob, "last_modified", None)
        url = f"{container.url}/{name}"
        await self.db.upsert_storage_cache({
          "user_guid": guid,
          "path": path,
          "filename": filename,
          "content_type": ct or "application/octet-stream",
          "public": 0,
          "created_on": created_on,
          "modified_on": modified_on,
          "url": url,
          "reported": 0,
          "moderation_recid": None,
        })
        seen.setdefault(guid, set()).add((path, filename))
      if user_guid:
        existing = await self.db.list_storage_cache(user_guid)
        for item in existing:
          if item.get("content_type") == "path/folder":
            continue
          key = (item["path"], item["filename"])
          if key not in seen.get(user_guid, set()):
            await self.db.delete_storage_cache(user_guid, item["path"], item["filename"])
      else:
        for guid, items_seen in seen.items():
          existing = await self.db.list_storage_cache(guid)
          for item in existing:
            if item.get("content_type") == "path/folder":
              continue
            key = (item["path"], item["filename"])
            if key not in items_seen:
              await self.db.delete_storage_cache(guid, item["path"], item["filename"])
    finally:
      await container.close()
      await bsc.close()

  async def upsert_file_record(self, user_guid: str, path: str, filename: str, file_type: str, **kwargs):
    """Upsert a file record into the ``users_storage_cache`` table."""
    assert self.db
    await self.db.upsert_storage_cache({
      "user_guid": user_guid,
      "path": path,
      "filename": filename,
      "content_type": file_type,
      "public": kwargs.get("public", 0),
      "created_on": kwargs.get("created_on"),
      "modified_on": kwargs.get("modified_on"),
      "url": kwargs.get("url"),
      "reported": kwargs.get("reported", 0),
      "moderation_recid": kwargs.get("moderation_recid"),
    })

  async def list_files_by_user(self, user_guid: str):
    """Return files belonging to ``user_guid``."""
    assert self.db
    rows = await self.db.list_storage_cache(user_guid)
    out = []
    for row in rows:
      if row.get("content_type") == "path/folder":
        continue
      path = row.get("path") or ""
      filename = row.get("filename", "")
      name = f"{path}/{filename}" if path else filename
      out.append({
        "name": name,
        "url": row.get("url") or name,
        "content_type": row.get("content_type"),
      })
    return out

  async def list_folder(self, user_guid: str, folder: str):
    """Return files and subfolders under ``folder`` for ``user_guid``."""
    assert self.db
    rows = await self.db.list_storage_cache(user_guid)
    folder = folder.strip("/")
    prefix = f"{folder}/" if folder else ""
    files: list[dict[str, str | None]] = []
    folders: dict[str, bool] = {}
    for row in rows:
      path = row.get("path") or ""
      filename = row.get("filename", "")
      ct = row.get("content_type")
      if ct == "path/folder":
        if path == folder:
          folders[filename] = True
        elif path.startswith(prefix):
          subfolder = path[len(prefix):].split("/", 1)[0]
          folders.setdefault(subfolder, True)
          folders[subfolder] = False
        continue
      if path == folder:
        name = f"{path}/{filename}" if path else filename
        files.append({
          "name": name,
          "url": row.get("url") or name,
          "content_type": ct,
        })
      elif path.startswith(prefix):
        subfolder = path[len(prefix):].split("/", 1)[0]
        folders.setdefault(subfolder, True)
        folders[subfolder] = False
    folder_items = [{"name": k, "empty": v} for k, v in folders.items()]
    return {"path": folder, "files": files, "folders": folder_items}

  async def list_public_files(self):
    """Return files marked as publicly accessible."""
    raise NotImplementedError

  async def list_flagged_for_moderation(self):
    """Return files that have been reported for moderation review."""
    raise NotImplementedError

  async def upload_files(self, user_guid: str, files):
    raise NotImplementedError

  async def delete_files(self, user_guid: str, names: list[str]):
    raise NotImplementedError

  async def set_gallery(self, user_guid: str, name: str, gallery: bool):
    raise NotImplementedError

  async def create_folder(self, user_guid: str, path: str):
    raise NotImplementedError

  async def delete_folder(self, user_guid: str, path: str):
    raise NotImplementedError

  async def create_user_folder(self, user_guid: str, path: str):
    raise NotImplementedError

  async def move_file(self, user_guid: str, src: str, dst: str):
    raise NotImplementedError

  async def get_file_link(self, user_guid: str, name: str) -> str:
    raise NotImplementedError

  async def rename_file(self, user_guid: str, old_name: str, new_name: str):
    raise NotImplementedError

  async def get_file_metadata(self, user_guid: str, name: str):
    raise NotImplementedError

  async def get_usage(self, user_guid: str):
    raise NotImplementedError

  async def get_storage_stats(self):
    assert self.db
    db_res = await self.db.run("db:storage:cache:count_rows:1", {})
    db_rows = db_res.rows[0]["count"] if db_res.rows else 0
    if not self.connection_string:
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "db_rows": db_rows,
      }
    res = await self.db.run("db:system:config:get_config:1", {"key": "AzureBlobContainerName"})
    container_name = res.rows[0]["value"] if res.rows else None
    if not container_name:
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "db_rows": db_rows,
      }
    bsc = BlobServiceClient.from_connection_string(self.connection_string)
    container = bsc.get_container_client(container_name)
    file_count = 0
    total_bytes = 0
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
        if parts[-1] == ".init":
          continue
        users.add(guid)
        file_count += 1
        size = getattr(blob, "size", None)
        if size is None:
          size = getattr(getattr(blob, "properties", None), "content_length", 0)
        total_bytes += size or 0
    finally:
      await container.close()
      await bsc.close()
    return {
      "file_count": file_count,
      "total_bytes": total_bytes,
      "folder_count": len(users),
      "db_rows": db_rows,
    }

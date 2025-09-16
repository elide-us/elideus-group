"""Storage management module for indexing Azure Blob contents."""

import asyncio, logging, re, base64
from typing import Any
from datetime import datetime, timezone
from uuid import UUID
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule
from .discord_module import DiscordModule


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
    self.discord: DiscordModule | None = None

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
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
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
    logging.info(
      "[StorageModule] Reindexing storage%s",
      f" for {user_guid}" if user_guid else " for all users",
    )
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
    files_seen: dict[str, set[tuple[str, str]]] = {}
    folder_seen: dict[str, set[tuple[str, str]]] = {}
    public_map: dict[str, dict[tuple[str, str], int]] = {}
    files_indexed = 0
    folders_indexed = 0
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
        path = "/".join(parts[1:-1])
        if guid not in public_map:
          rows = await self.db.list_storage_cache(guid)
          public_map[guid] = {
            (r.get("path") or "", r.get("filename")): r.get("public", 0)
            for r in rows
            if r.get("content_type") != "path/folder"
          }
        # index folders along the path (up to 4 levels)
        parent = ""
        fset = folder_seen.setdefault(guid, set())
        for folder_name in parts[1:-1][:4]:
          key = (parent, folder_name)
          if key not in fset:
            logging.debug(
              "[StorageModule] indexing folder %s/%s", parent or ".", folder_name
            )
            res = await self.db.upsert_storage_cache({
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
            if res.rowcount == 0:
              logging.error(
                "[StorageModule] Failed to upsert folder %s/%s",
                parent or ".",
                folder_name,
              )
            fset.add(key)
            folders_indexed += 1
          parent = f"{parent}/{folder_name}" if parent else folder_name
        # handle explicit folder markers (Azure Storage Explorer etc.)
        meta = getattr(blob, "metadata", {}) or {}
        if meta.get("hdi_isfolder") == "true":
          key = (path, filename)
          if key not in fset:
            logging.debug(
              "[StorageModule] indexing folder %s/%s", path or ".", filename
            )
            res = await self.db.upsert_storage_cache({
              "user_guid": guid,
              "path": path,
              "filename": filename,
              "content_type": "path/folder",
              "public": 0,
              "created_on": None,
              "modified_on": None,
              "url": None,
              "reported": 0,
              "moderation_recid": None,
            })
            if res.rowcount == 0:
              logging.error(
                "[StorageModule] Failed to upsert folder %s/%s",
                path or ".",
                filename,
              )
            fset.add(key)
            folders_indexed += 1
          continue
        if not filename or filename == ".init":
          continue
        ct = None
        if hasattr(blob, "content_settings") and blob.content_settings:
          ct = getattr(blob.content_settings, "content_type", None)
        if not ct:
          ct = getattr(blob, "content_type", None)
        created_on = getattr(blob, "creation_time", None) or getattr(blob, "created_on", None)
        modified_on = getattr(blob, "last_modified", None)
        url = f"{container.url}/{name}"
        logging.debug(
          "[StorageModule] indexing file %s/%s", path or ".", filename
        )
        public_val = public_map.get(guid, {}).get((path, filename), 0)
        res = await self.db.upsert_storage_cache({
          "user_guid": guid,
          "path": path,
          "filename": filename,
          "content_type": ct or "application/octet-stream",
          "public": public_val,
          "created_on": created_on,
          "modified_on": modified_on,
          "url": url,
          "reported": 0,
          "moderation_recid": None,
        })
        if res.rowcount == 0:
          logging.error(
            "[StorageModule] Failed to upsert file %s/%s",
            path or ".",
            filename,
          )
        files_seen.setdefault(guid, set()).add((path, filename))
        public_map.setdefault(guid, {})[(path, filename)] = public_val
        files_indexed += 1
      if user_guid:
        existing = public_map.get(user_guid, {})
        for key in list(existing.keys()):
          if key not in files_seen.get(user_guid, set()):
            await self.db.delete_storage_cache(user_guid, key[0], key[1])
      else:
        for guid, items_seen in files_seen.items():
          existing = public_map.get(guid, {})
          for key in list(existing.keys()):
            if key not in items_seen:
              await self.db.delete_storage_cache(guid, key[0], key[1])
    finally:
      logging.debug(
        "[StorageModule] Reindex found %d files and %d folders%s",
        files_indexed,
        folders_indexed,
        f" for {user_guid}" if user_guid else "",
      )
      await container.close()
      await bsc.close()
      logging.info(
        "[StorageModule] Reindex complete%s",
        f" for {user_guid}" if user_guid else "",
      )

  async def upsert_file_record(self, user_guid: str, path: str, filename: str, file_type: str, **kwargs):
    """Upsert a file record into the ``users_storage_cache`` table."""
    assert self.db
    res = await self.db.upsert_storage_cache({
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
    if res.rowcount == 0:
      logging.error(
        "[StorageModule] Failed to upsert file %s/%s",
        path or ".",
        filename,
      )

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
      full_name = f"{path}/{filename}" if path else filename
      out.append({
        "path": path,
        "name": filename,
        "url": row.get("url") or full_name,
        "content_type": row.get("content_type"),
        "gallery": bool(row.get("public")),
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
        full_name = f"{path}/{filename}" if path else filename
        files.append({
          "path": path,
          "name": filename,
          "url": row.get("url") or full_name,
          "content_type": ct,
          "gallery": bool(row.get("public")),
        })
      elif path.startswith(prefix):
        subfolder = path[len(prefix):].split("/", 1)[0]
        folders.setdefault(subfolder, True)
        folders[subfolder] = False
    folder_items = [{"name": k, "empty": v} for k, v in folders.items()]
    return {"path": folder, "files": files, "folders": folder_items}

  async def list_public_files(self):
    """Return files marked as publicly accessible."""
    assert self.db
    res = await self.db.run("db:storage:cache:list_public:1", {})
    return res.rows

  async def list_flagged_for_moderation(self):
    """Return files that have been reported for moderation review."""
    assert self.db
    res = await self.db.run("db:storage:cache:list_reported:1", {})
    return res.rows

  async def upload_files(self, user_guid: str, files):
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
    try:
      for f in files:
        name = getattr(f, "name", None)
        if not name and isinstance(f, dict):
          name = f.get("name")
        content_b64 = getattr(f, "content_b64", None)
        if not content_b64 and isinstance(f, dict):
          content_b64 = f.get("content_b64")
        if not name or not content_b64:
          continue
        blob_name = f"{user_guid}/{name.lstrip('/')}"
        data = base64.b64decode(content_b64)
        ct = getattr(f, "content_type", None)
        if ct is None and isinstance(f, dict):
          ct = f.get("content_type")
        try:
          await container.upload_blob(
            blob_name,
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=ct) if ct else None,
          )
        except Exception as e:
          logging.error("[StorageModule] Failed to upload %s: %s", blob_name, e)
          continue
        now = datetime.now(timezone.utc)
        path = "/".join(name.split("/")[:-1])
        filename = name.split("/")[-1]
        url = f"{container.url}/{blob_name}"
        try:
          res = await self.db.upsert_storage_cache({
            "user_guid": user_guid,
            "path": path,
            "filename": filename,
            "content_type": ct or "application/octet-stream",
            "public": 0,
            "created_on": now,
            "modified_on": now,
            "url": url,
            "reported": 0,
            "moderation_recid": None,
          })
          if res.rowcount == 0:
            logging.error("[StorageModule] Failed to upsert file %s/%s", path or '.', filename)
        except Exception as e:
          logging.error("[StorageModule] Failed to update cache for %s/%s: %s", path or '.', filename, e)
    finally:
      await container.close()
      await bsc.close()

  async def delete_files(self, user_guid: str, names: list[str]):
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
    try:
      for name in names:
        blob_name = f"{user_guid}/{name.lstrip('/')}"
        path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
        blob = container.get_blob_client(blob_name)
        try:
          await blob.delete_blob()
        except Exception as e:
          logging.error("[StorageModule] Failed to delete %s: %s", blob_name, e)
        try:
          await self.db.delete_storage_cache(user_guid, path, filename)
        except Exception as e:
          logging.error(
            "[StorageModule] Failed to delete cache for %s/%s: %s",
            path or '.',
            filename,
            e,
          )
    finally:
      await container.close()
      await bsc.close()

  async def set_gallery(self, user_guid: str, name: str, gallery: bool):
    assert self.db
    await self.db.run(
      "db:storage:files:set_gallery:1",
      {"user_guid": user_guid, "name": name, "gallery": 1 if gallery else 0},
    )

  async def report_file(self, user_guid: str, name: str):
    assert self.db
    path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
    await self.db.run(
      "db:storage:cache:set_reported:1",
      {"user_guid": user_guid, "path": path, "filename": filename, "reported": 1},
    )

  async def create_folder(self, user_guid: str, path: str):
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
    folder_path = path.lstrip("/")
    blob_name = f"{user_guid}/{folder_path}"
    init_name = f"{blob_name}/.init"
    parent, folder_name = folder_path.rsplit("/", 1) if "/" in folder_path else ("", folder_path)
    try:
      await container.upload_blob(
        blob_name,
        b"",
        metadata={"hdi_isfolder": "true"},
        overwrite=True,
      )
      await container.upload_blob(
        init_name,
        b"",
        overwrite=True,
      )
      try:
        await self.db.upsert_storage_cache({
          "user_guid": user_guid,
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
      except Exception as e:
        logging.error(
          "[StorageModule] Failed to update cache for %s/%s: %s",
          parent or ".",
          folder_name,
          e,
        )
    finally:
      await container.close()
      await bsc.close()

  async def delete_folder(self, user_guid: str, path: str):
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
    prefix = f"{user_guid}/{path.lstrip('/')}"
    try:
      async for blob in container.list_blobs(name_starts_with=prefix):
        try:
          await container.delete_blob(blob.name)
        except Exception as e:
          logging.error("[StorageModule] Failed to delete %s: %s", blob.name, e)
        parts = blob.name.split("/")
        if len(parts) < 2:
          continue
        file_path = "/".join(parts[1:-1])
        filename = parts[-1]
        try:
          await self.db.delete_storage_cache(user_guid, file_path, filename)
        except Exception as e:
          logging.error(
            "[StorageModule] Failed to delete cache for %s/%s: %s",
            file_path or '.',
            filename,
            e,
          )
      await self.db.delete_storage_cache_folder(user_guid, path.lstrip('/'))
    finally:
      await container.close()
      await bsc.close()

  async def create_user_folder(self, user_guid: str, path: str):
    await self.create_folder(user_guid, path)

  async def move_file(self, user_guid: str, src: str, dst: str):
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
    src_blob_name = f"{user_guid}/{src.lstrip('/')}"
    dst_blob_name = f"{user_guid}/{dst.lstrip('/')}"
    src_path, src_filename = src.rsplit('/', 1) if '/' in src else ('', src)
    dst_path, dst_filename = dst.rsplit('/', 1) if '/' in dst else ('', dst)
    src_blob = container.get_blob_client(src_blob_name)
    dst_blob = container.get_blob_client(dst_blob_name)
    try:
      props = await src_blob.get_blob_properties()
      await dst_blob.start_copy_from_url(src_blob.url)
      await src_blob.delete_blob()
      await self.db.delete_storage_cache(user_guid, src_path, src_filename)
      ct = None
      if getattr(props, "content_settings", None):
        ct = getattr(props.content_settings, "content_type", None)
      created_on = getattr(props, "creation_time", None) or getattr(props, "created_on", None)
      modified_on = getattr(props, "last_modified", None)
      await self.db.upsert_storage_cache({
        "user_guid": user_guid,
        "path": dst_path,
        "filename": dst_filename,
        "content_type": ct or "application/octet-stream",
        "public": 0,
        "created_on": created_on,
        "modified_on": modified_on,
        "url": dst_blob.url,
        "reported": 0,
        "moderation_recid": None,
      })
    except Exception as e:
      logging.error("[StorageModule] Failed to move %s to %s: %s", src, dst, e)
    finally:
      await container.close()
      await bsc.close()

  async def _update_cache_entry(
    self,
    container: Any,
    user_guid: str,
    old_rel: str,
    new_rel: str,
    cache_entry: dict[str, Any] | None,
    props: Any,
    dest_url: str | None,
  ):
    if not self.db:
      return
    old_path, old_filename = old_rel.rsplit("/", 1) if "/" in old_rel else ("", old_rel)
    new_path, new_filename = new_rel.rsplit("/", 1) if "/" in new_rel else ("", new_rel)
    try:
      await self.db.delete_storage_cache(user_guid, old_path, old_filename)
    except Exception as e:
      logging.error(
        "[StorageModule] Failed to delete cache for %s/%s: %s",
        old_path or '.',
        old_filename,
        e,
      )
    if cache_entry is None:
      return
    ct = cache_entry.get("content_type") or "application/octet-stream"
    if props is not None and getattr(props, "content_settings", None):
      ct = getattr(props.content_settings, "content_type", None) or ct
    created_on = cache_entry.get("created_on")
    modified_on = cache_entry.get("modified_on")
    if props is not None:
      created_on = (
        getattr(props, "creation_time", None)
        or getattr(props, "created_on", None)
        or created_on
      )
      modified_on = getattr(props, "last_modified", None) or modified_on
    url = dest_url
    if url is None:
      existing = cache_entry.get("url")
      if existing:
        base = getattr(container, "url", "").rstrip("/")
        rel = f"{user_guid}/{new_rel}".lstrip("/")
        url = f"{base}/{rel}" if base else existing
    try:
      await self.db.upsert_storage_cache({
        "user_guid": user_guid,
        "path": new_path,
        "filename": new_filename,
        "content_type": ct,
        "public": 1 if cache_entry.get("public") else 0,
        "created_on": created_on,
        "modified_on": modified_on,
        "url": url,
        "reported": cache_entry.get("reported", 0),
        "moderation_recid": cache_entry.get("moderation_recid"),
      })
    except Exception as e:
      logging.error(
        "[StorageModule] Failed to update cache for %s/%s: %s",
        new_path or '.',
        new_filename,
        e,
      )

  async def _rename_single_blob(
    self,
    container: Any,
    user_guid: str,
    old_rel: str,
    new_rel: str,
    cache_entry: dict[str, Any] | None,
    processed: set[str],
  ):
    if old_rel == new_rel:
      return
    src_name = f"{user_guid}/{old_rel}"
    dst_name = f"{user_guid}/{new_rel}"
    src_blob = container.get_blob_client(src_name)
    dst_blob = container.get_blob_client(dst_name)
    try:
      src_exists = await src_blob.exists()
    except Exception as e:
      logging.error("[StorageModule] Failed to check blob %s: %s", src_name, e)
      src_exists = False
    if not src_exists:
      if cache_entry is not None:
        await self._update_cache_entry(container, user_guid, old_rel, new_rel, cache_entry, None, None)
        processed.add(old_rel)
      return
    try:
      if await dst_blob.exists():
        logging.error(
          "[StorageModule] Destination blob already exists for rename %s -> %s",
          old_rel,
          new_rel,
        )
        return
    except Exception as e:
      logging.error("[StorageModule] Failed to check destination blob %s: %s", dst_name, e)
      return
    try:
      props = await src_blob.get_blob_properties()
      await dst_blob.start_copy_from_url(src_blob.url)
      await src_blob.delete_blob()
      await self._update_cache_entry(
        container,
        user_guid,
        old_rel,
        new_rel,
        cache_entry,
        props,
        dst_blob.url,
      )
      if cache_entry is not None:
        processed.add(old_rel)
    except Exception as e:
      logging.error(
        "[StorageModule] Failed to rename blob %s to %s: %s",
        old_rel,
        new_rel,
        e,
      )

  async def _rename_folder_contents(
    self,
    container: Any,
    user_guid: str,
    old_rel: str,
    new_rel: str,
    cache_map: dict[str, dict[str, Any]],
    processed: set[str],
  ):
    if new_rel.startswith(f"{old_rel}/"):
      logging.error(
        "[StorageModule] Cannot rename folder %s into its own child %s",
        old_rel,
        new_rel,
      )
      return
    dst_prefix = f"{user_guid}/{new_rel}"
    dst_placeholder = container.get_blob_client(dst_prefix)
    try:
      if await dst_placeholder.exists():
        logging.error("[StorageModule] Target folder %s already exists", new_rel)
        return
    except Exception as e:
      logging.error("[StorageModule] Failed to check destination folder %s: %s", dst_prefix, e)
      return
    try:
      async for _ in container.list_blobs(name_starts_with=f"{dst_prefix}/"):
        logging.error("[StorageModule] Target folder %s already contains blobs", new_rel)
        return
    except Exception as e:
      logging.error("[StorageModule] Failed to inspect destination folder %s: %s", dst_prefix, e)
      return
    await self._rename_single_blob(
      container,
      user_guid,
      old_rel,
      new_rel,
      cache_map.get(old_rel),
      processed,
    )
    src_prefix = f"{user_guid}/{old_rel}"
    try:
      async for blob in container.list_blobs(name_starts_with=f"{src_prefix}/"):
        rel_name = blob.name[len(f"{user_guid}/"):]
        if not rel_name:
          continue
        suffix = rel_name[len(old_rel):]
        new_rel_name = f"{new_rel}{suffix}"
        await self._rename_single_blob(
          container,
          user_guid,
          rel_name,
          new_rel_name,
          cache_map.get(rel_name),
          processed,
        )
    except Exception as e:
      logging.error("[StorageModule] Failed to list blobs for folder %s: %s", old_rel, e)
    prefix = f"{old_rel}/"
    for full, entry in cache_map.items():
      if full == old_rel or full.startswith(prefix):
        if full in processed:
          continue
        new_full = f"{new_rel}{full[len(old_rel):]}"
        await self._update_cache_entry(
          container,
          user_guid,
          full,
          new_full,
          entry,
          None,
          None,
        )
        processed.add(full)

  async def get_file_link(self, user_guid: str, name: str) -> str:
    raise NotImplementedError

  async def rename_file(self, user_guid: str, old_name: str, new_name: str):
    if not self.connection_string or not self.db:
      logging.error("[StorageModule] Missing connection string or database module")
      return
    res = await self.db.run("db:system:config:get_config:1", {"key": "AzureBlobContainerName"})
    container_name = res.rows[0]["value"] if res.rows else None
    if not container_name:
      logging.error("[StorageModule] AzureBlobContainerName missing")
      return
    old_rel = (old_name or "").strip("/")
    new_rel = (new_name or "").strip("/")
    if not old_rel or not new_rel:
      logging.error("[StorageModule] Invalid rename request %s -> %s", old_name, new_name)
      return
    if old_rel == new_rel:
      return
    bsc = BlobServiceClient.from_connection_string(self.connection_string)
    container = bsc.get_container_client(container_name)
    cache_rows = await self.db.list_storage_cache(user_guid)
    cache_map: dict[str, dict[str, Any]] = {}
    for row in cache_rows:
      path = row.get("path") or ""
      filename = row.get("filename") or ""
      full = f"{path}/{filename}" if path else filename
      cache_map[full] = row
    processed: set[str] = set()
    try:
      entry = cache_map.get(old_rel)
      is_folder = bool(entry and entry.get("content_type") == "path/folder")
      if not is_folder:
        src_prefix = f"{user_guid}/{old_rel}"
        try:
          async for _ in container.list_blobs(name_starts_with=f"{src_prefix}/"):
            is_folder = True
            break
        except Exception as e:
          logging.error("[StorageModule] Failed to inspect folder %s: %s", old_rel, e)
        if not is_folder:
          try:
            props = await container.get_blob_client(src_prefix).get_blob_properties()
            metadata = getattr(props, "metadata", {}) or {}
            if metadata.get("hdi_isfolder") == "true":
              is_folder = True
          except Exception:
            pass
      if is_folder:
        await self._rename_folder_contents(container, user_guid, old_rel, new_rel, cache_map, processed)
      else:
        await self._rename_single_blob(
          container,
          user_guid,
          old_rel,
          new_rel,
          entry,
          processed,
        )
    except Exception as e:
      logging.error("[StorageModule] Failed to rename %s to %s: %s", old_name, new_name, e)
    finally:
      await container.close()
      await bsc.close()

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
        "user_folder_count": 0,
        "db_rows": db_rows,
      }
    res = await self.db.run("db:system:config:get_config:1", {"key": "AzureBlobContainerName"})
    container_name = res.rows[0]["value"] if res.rows else None
    if not container_name:
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "user_folder_count": 0,
        "db_rows": db_rows,
      }
    bsc = BlobServiceClient.from_connection_string(self.connection_string)
    container = bsc.get_container_client(container_name)
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
          size = getattr(getattr(blob, "properties", None), "content_length", 0)
        total_bytes += size or 0
    finally:
      await container.close()
      await bsc.close()
    return {
      "file_count": file_count,
      "total_bytes": total_bytes,
      "folder_count": len(folders),
      "user_folder_count": len(users),
      "db_rows": db_rows,
    }

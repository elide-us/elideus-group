"""Storage management module for indexing Azure Blob contents."""

import asyncio, logging, re, base64
from typing import Any
from datetime import datetime, timezone
from uuid import UUID
from fastapi import FastAPI
from server.registry.system.config.model import ConfigKeyParams
from server.modules.registry.helpers import (
  count_rows_request,
  get_config_request,
  list_public_request,
  list_reported_request,
  set_gallery_request,
  set_reported_request,
)
from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from .providers.storage import (
  StorageBlobProperties,
  StorageCreateFolderRequest,
  StorageDeleteFolderRequest,
  StorageDeleteRequest,
  StorageMoveRequest,
  StorageRenameRequest,
  StorageReindexRequest,
  StorageUploadFile,
  StorageUploadRequest,
  StorageStatsRequest,
)
from .providers.storage.azure_blob_provider import AzureBlobStorageProvider


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
    self.discord: DiscordBotModule | None = None
    self.provider: AzureBlobStorageProvider | None = None

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
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    try:
      self.connection_string = self.env.get("AZURE_BLOB_CONNECTION_STRING")
      if not self.connection_string:
        logging.error("[StorageModule] AZURE_BLOB_CONNECTION_STRING missing")
        self.provider = None
      else:
        self.provider = AzureBlobStorageProvider(connection_string=self.connection_string)
        await self.provider.startup()
    except Exception as e:
      logging.error("[StorageModule] Failed to load AZURE_BLOB_CONNECTION_STRING: %s", e)
      self.provider = None

    try:
      res = await self.db.run(get_config_request(ConfigKeyParams(key="StorageCacheTime")))
      value = res.rows[0]["value"] if res.rows else "15m"
      try:
        self.reindex_interval = self._parse_duration(value)
      except Exception:
        logging.error("[StorageModule] Invalid StorageCacheTime '%s'", value)
    except Exception as e:
      logging.error("[StorageModule] Failed to load StorageCacheTime: %s", e)
    self._reindex_task = asyncio.create_task(self._reindex_loop())
    logging.debug("Storage module loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._reindex_task:
      self._reindex_task.cancel()
      try:
        await self._reindex_task
      except asyncio.CancelledError:
        pass
      self._reindex_task = None
    if self.provider:
      try:
        await self.provider.shutdown()
      except Exception as exc:
        logging.error("[StorageModule] Provider shutdown failed: %s", exc)
      self.provider = None

  async def _reindex_loop(self):
    while True:
      await asyncio.sleep(self.reindex_interval)
      try:
        await self.reindex()
      except Exception as e:
        logging.error("[StorageModule] Reindex failed: %s", e)

  def _require_provider(self) -> AzureBlobStorageProvider | None:
    if not self.provider:
      logging.error("[StorageModule] Storage provider is not configured")
      return None
    return self.provider

  async def _get_container_name(self) -> str | None:
    if not self.db:
      logging.error("[StorageModule] Database module unavailable")
      return None
    res = await self.db.run(get_config_request(ConfigKeyParams(key="AzureBlobContainerName")))
    container_name = res.rows[0]["value"] if res.rows else None
    if not container_name:
      logging.error("[StorageModule] AzureBlobContainerName missing")
    return container_name

  async def reindex(self, user_guid: str | None = None):
    """Perform a scan of storage and update database cache."""
    logging.info(
      "[StorageModule] Reindexing storage%s",
      f" for {user_guid}" if user_guid else " for all users",
    )
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    valid_users: set[str] = set()
    missing_users: set[str] = set()

    async def ensure_user(guid: str) -> bool:
      if guid in valid_users:
        return True
      if guid in missing_users:
        return False
      try:
        exists = await self.db.user_exists(guid)
      except Exception as exc:
        logging.error("[StorageModule] Failed to validate user %s: %s", guid, exc)
        missing_users.add(guid)
        return False
      if not exists:
        logging.warning("[StorageModule] Skipping blob for unknown user %s", guid)
        missing_users.add(guid)
        return False
      valid_users.add(guid)
      return True

    if user_guid:
      if not await ensure_user(user_guid):
        return

    prefix = f"{user_guid}/" if user_guid else None
    response = await provider.reindex(
      StorageReindexRequest(container_name=container_name, prefix=prefix)
    )
    files_seen: dict[str, set[tuple[str, str]]] = {}
    folder_seen: dict[str, set[tuple[str, str]]] = {}
    public_map: dict[str, dict[tuple[str, str], int]] = {}
    files_indexed = 0
    folders_indexed = 0

    for blob in response.blobs:
      name = blob.name
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
      if not await ensure_user(guid):
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
      if blob.is_directory:
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
      ct = blob.content_type or "application/octet-stream"
      created_on = blob.created_on
      modified_on = blob.modified_on
      url = blob.url or f"{response.container_url}/{name}"
      logging.debug(
        "[StorageModule] indexing file %s/%s", path or ".", filename
      )
      public_val = public_map.get(guid, {}).get((path, filename), 0)
      res = await self.db.upsert_storage_cache({
        "user_guid": guid,
        "path": path,
        "filename": filename,
        "content_type": ct,
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

    logging.debug(
      "[StorageModule] Reindex found %d files and %d folders%s",
      files_indexed,
      folders_indexed,
      f" for {user_guid}" if user_guid else "",
    )
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
    res = await self.db.run(list_public_request())
    return res.rows

  async def list_flagged_for_moderation(self):
    """Return files that have been reported for moderation review."""
    assert self.db
    res = await self.db.run(list_reported_request())
    return res.rows

  async def upload_files(self, user_guid: str, files):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    payload: list[StorageUploadFile] = []
    for f in files:
      name = getattr(f, "name", None)
      if not name and isinstance(f, dict):
        name = f.get("name")
      content_b64 = getattr(f, "content_b64", None)
      if not content_b64 and isinstance(f, dict):
        content_b64 = f.get("content_b64")
      if not name or not content_b64:
        continue
      ct = getattr(f, "content_type", None)
      if ct is None and isinstance(f, dict):
        ct = f.get("content_type")
      try:
        data = base64.b64decode(content_b64)
      except Exception as exc:
        logging.error("[StorageModule] Failed to decode upload for %s: %s", name, exc)
        continue
      normalized = name.lstrip("/")
      payload.append(
        StorageUploadFile(
          blob_name=f"{user_guid}/{normalized}",
          relative_path=normalized,
          data=data,
          content_type=ct,
        )
      )
    if not payload:
      return
    response = await provider.upload_files(
      StorageUploadRequest(container_name=container_name, files=payload)
    )
    for rel, err in response.errors.items():
      logging.error("[StorageModule] Failed to upload %s: %s", rel, err)
    for result in response.results:
      name = result.relative_path.lstrip("/")
      path = "/".join(name.split("/")[:-1])
      filename = name.split("/")[-1]
      try:
        res = await self.db.upsert_storage_cache({
          "user_guid": user_guid,
          "path": path,
          "filename": filename,
          "content_type": result.content_type or "application/octet-stream",
          "public": 0,
          "created_on": result.created_on,
          "modified_on": result.modified_on,
          "url": result.url,
          "reported": 0,
          "moderation_recid": None,
        })
        if res.rowcount == 0:
          logging.error(
            "[StorageModule] Failed to upsert file %s/%s",
            path or ".",
            filename,
          )
      except Exception as exc:
        logging.error(
          "[StorageModule] Failed to update cache for %s/%s: %s",
          path or ".",
          filename,
          exc,
        )

  async def delete_files(self, user_guid: str, names: list[str]):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    normalized = [name.lstrip("/") for name in names]
    blob_names = [f"{user_guid}/{name}" for name in normalized]
    response = await provider.delete_files(
      StorageDeleteRequest(
        container_name=container_name,
        blob_names=blob_names,
        relative_paths=normalized,
      )
    )
    for rel, err in response.errors.items():
      logging.error("[StorageModule] Failed to delete %s: %s", rel, err)
    for rel in response.deleted:
      path, filename = rel.rsplit("/", 1) if "/" in rel else ("", rel)
      try:
        await self.db.delete_storage_cache(user_guid, path, filename)
      except Exception as exc:
        logging.error(
          "[StorageModule] Failed to delete cache for %s/%s: %s",
          path or ".",
          filename,
          exc,
        )

  async def set_gallery(self, user_guid: str, name: str, gallery: bool):
    assert self.db
    await self.db.run(set_gallery_request(user_guid, name, gallery))

  async def report_file(self, user_guid: str, name: str):
    assert self.db
    path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
    await self.db.run(set_reported_request(user_guid, path=path, filename=filename, reported=True))

  async def create_folder(self, user_guid: str, path: str):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    folder_path = path.lstrip("/")
    blob_name = f"{user_guid}/{folder_path}"
    init_name = f"{blob_name}/.init"
    try:
      result = await provider.create_folder(
        StorageCreateFolderRequest(
          container_name=container_name,
          blob_name=blob_name,
          init_blob_name=init_name,
        )
      )
    except Exception as exc:
      logging.error("[StorageModule] Failed to create folder %s: %s", path, exc)
      return
    relative = result.relative_path
    parent, folder_name = relative.rsplit("/", 1) if "/" in relative else ("", relative)
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
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to update cache for %s/%s: %s",
        parent or ".",
        folder_name,
        exc,
      )

  async def delete_folder(self, user_guid: str, path: str):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    normalized = path.lstrip("/")
    prefix = f"{user_guid}/{normalized}" if normalized else user_guid
    response = await provider.delete_folder(
      StorageDeleteFolderRequest(
        container_name=container_name,
        user_guid=user_guid,
        prefix=prefix,
      )
    )
    for rel, err in response.errors.items():
      logging.error("[StorageModule] Failed to delete folder entry %s: %s", rel, err)
    for entry in response.deleted_entries:
      rel = entry.relative_path
      if not rel:
        continue
      file_path, filename = rel.rsplit("/", 1) if "/" in rel else ("", rel)
      try:
        await self.db.delete_storage_cache(user_guid, file_path, filename)
      except Exception as exc:
        logging.error(
          "[StorageModule] Failed to delete cache for %s/%s: %s",
          file_path or ".",
          filename,
          exc,
        )
    try:
      await self.db.delete_storage_cache_folder(user_guid, normalized)
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to delete folder cache for %s/%s: %s",
        user_guid,
        normalized,
        exc,
      )

  async def create_user_folder(self, user_guid: str, path: str):
    await self.create_folder(user_guid, path)

  async def move_file(self, user_guid: str, src: str, dst: str):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    normalized_src = src.lstrip("/")
    normalized_dst = dst.lstrip("/")
    result = await provider.move_file(
      StorageMoveRequest(
        container_name=container_name,
        src_blob=f"{user_guid}/{normalized_src}",
        dst_blob=f"{user_guid}/{normalized_dst}",
        src_relative=normalized_src,
        dst_relative=normalized_dst,
      )
    )
    if not result:
      return
    src_path, src_filename = normalized_src.rsplit("/", 1) if "/" in normalized_src else ("", normalized_src)
    dst_path, dst_filename = normalized_dst.rsplit("/", 1) if "/" in normalized_dst else ("", normalized_dst)
    try:
      await self.db.delete_storage_cache(user_guid, src_path, src_filename)
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to delete cache for %s/%s: %s",
        src_path or ".",
        src_filename,
        exc,
      )
    props = result.properties
    try:
      await self.db.upsert_storage_cache({
        "user_guid": user_guid,
        "path": dst_path,
        "filename": dst_filename,
        "content_type": props.content_type or "application/octet-stream",
        "public": 0,
        "created_on": props.created_on,
        "modified_on": props.modified_on,
        "url": result.url,
        "reported": 0,
        "moderation_recid": None,
      })
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to update cache for %s/%s: %s",
        dst_path or ".",
        dst_filename,
        exc,
      )

  async def get_file_link(self, user_guid: str, name: str) -> str:
    raise NotImplementedError

  async def _update_cache_entry(
    self,
    user_guid: str,
    old_rel: str,
    new_rel: str,
    cache_entry: dict[str, Any] | None,
    properties: StorageBlobProperties | None,
    container_url: str | None,
    dest_url: str | None,
  ):
    if not self.db:
      return
    old_path, old_filename = old_rel.rsplit("/", 1) if "/" in old_rel else ("", old_rel)
    new_path, new_filename = new_rel.rsplit("/", 1) if "/" in new_rel else ("", new_rel)
    try:
      await self.db.delete_storage_cache(user_guid, old_path, old_filename)
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to delete cache for %s/%s: %s",
        old_path or ".",
        old_filename,
        exc,
      )
    if cache_entry is None:
      return
    ct = cache_entry.get("content_type") or "application/octet-stream"
    if properties and properties.content_type:
      ct = properties.content_type or ct
    created_on = cache_entry.get("created_on")
    modified_on = cache_entry.get("modified_on")
    if properties:
      created_on = properties.created_on or created_on
      modified_on = properties.modified_on or modified_on
    url = dest_url or cache_entry.get("url")
    if not url and container_url:
      rel = f"{user_guid}/{new_rel}".lstrip("/")
      base = container_url.rstrip("/")
      if base and rel:
        url = f"{base}/{rel}"
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
    except Exception as exc:
      logging.error(
        "[StorageModule] Failed to update cache for %s/%s: %s",
        new_path or ".",
        new_filename,
        exc,
      )

  async def rename_file(self, user_guid: str, old_name: str, new_name: str):
    if not self.db:
      logging.error("[StorageModule] Missing database module")
      return
    provider = self._require_provider()
    if not provider:
      return
    container_name = await self._get_container_name()
    if not container_name:
      return
    old_rel = (old_name or "").strip("/")
    new_rel = (new_name or "").strip("/")
    if not old_rel or not new_rel:
      logging.error("[StorageModule] Invalid rename request %s -> %s", old_name, new_name)
      return
    if old_rel == new_rel:
      return
    cache_rows = await self.db.list_storage_cache(user_guid)
    cache_map: dict[str, dict[str, Any]] = {}
    for row in cache_rows:
      path = row.get("path") or ""
      filename = row.get("filename") or ""
      full = f"{path}/{filename}" if path else filename
      cache_map[full] = row
    entry = cache_map.get(old_rel)
    is_folder = bool(entry and entry.get("content_type") == "path/folder")
    if not is_folder:
      prefix = f"{old_rel}/"
      for key in cache_map.keys():
        if key.startswith(prefix):
          is_folder = True
          break
    try:
      response = await provider.rename_file(
        StorageRenameRequest(
          container_name=container_name,
          user_guid=user_guid,
          old_relative=old_rel,
          new_relative=new_rel,
          is_folder=is_folder,
        )
      )
    except Exception as exc:
      logging.error("[StorageModule] Failed to rename %s to %s: %s", old_name, new_name, exc)
      return
    for err in response.errors:
      logging.error("[StorageModule] Provider rename error: %s", err)
    processed: set[str] = set()
    for op in response.operations:
      cache_entry = cache_map.get(op.old_relative)
      await self._update_cache_entry(
        user_guid,
        op.old_relative,
        op.new_relative,
        cache_entry,
        op.properties if not op.source_missing else None,
        response.container_url or None,
        op.url,
      )
      if cache_entry is not None:
        processed.add(op.old_relative)
    if is_folder:
      prefix = f"{old_rel}/"
      for full, cache_entry in cache_map.items():
        if full == old_rel or full.startswith(prefix):
          if full in processed:
            continue
          new_full = f"{new_rel}{full[len(old_rel):]}" if full != old_rel else new_rel
          await self._update_cache_entry(
            user_guid,
            full,
            new_full,
            cache_entry,
            None,
            response.container_url or None,
            None,
          )
          processed.add(full)

  async def get_file_metadata(self, user_guid: str, name: str):
    raise NotImplementedError

  async def get_usage(self, user_guid: str):
    raise NotImplementedError

  async def get_storage_stats(self):
    assert self.db
    db_res = await self.db.run(count_rows_request())
    db_rows = db_res.rows[0]["count"] if db_res.rows else 0
    provider = self._require_provider()
    if not provider:
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "user_folder_count": 0,
        "db_rows": db_rows,
      }
    container_name = await self._get_container_name()
    if not container_name:
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "user_folder_count": 0,
        "db_rows": db_rows,
      }
    try:
      stats = await provider.get_storage_stats(
        StorageStatsRequest(container_name=container_name)
      )
    except Exception as exc:
      logging.error("[StorageModule] Failed to fetch storage stats: %s", exc)
      return {
        "file_count": 0,
        "total_bytes": 0,
        "folder_count": 0,
        "user_folder_count": 0,
        "db_rows": db_rows,
      }
    return {
      "file_count": stats.file_count,
      "total_bytes": stats.total_bytes,
      "folder_count": len(stats.folder_paths),
      "user_folder_count": len(stats.user_ids),
      "db_rows": db_rows,
    }

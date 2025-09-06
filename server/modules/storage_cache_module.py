"""Storage cache module."""

from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .storage_module import StorageModule
import logging


class StorageCacheModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.storage: StorageModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.storage = self.app.state.storage
    await self.storage.on_ready()
    self.mark_ready()

  async def shutdown(self):
    logging.info("Storage cache module shutdown")

  async def list_user_files(self, user_guid: str) -> list[dict[str, str | None]]:
    assert self.db and self.storage
    rows = await self.db.list_storage_cache(user_guid)
    files: list[dict[str, str | None]] = []
    base = self.storage.client.url if self.storage.client else ""
    for row in rows:
      path = row.get("path") or ""
      filename = row.get("filename") or ""
      name = f"{path}/{filename}" if path else filename
      url = f"{base}/{user_guid}/{name}" if base else ""
      files.append({"name": name, "url": url, "content_type": row.get("content_type")})
    return files

  async def refresh_user_cache(self, user_guid: str) -> list[dict[str, str | None]]:
    assert self.db and self.storage
    files = await self.storage.list_user_files(user_guid)
    items = []
    for f in files:
      name = f.get("name", "")
      path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
      items.append({
        "path": path,
        "filename": filename,
        "public": 0,
        "content_type": f.get("content_type"),
        "deleted": 0,
      })
    await self.db.replace_storage_cache(user_guid, items)
    return await self.list_user_files(user_guid)

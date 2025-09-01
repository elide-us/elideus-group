from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvModule
from .db_module import DbModule
import io, logging

class StorageModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.client: ContainerClient = None
    self.container = ""

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()

    dsn = self.env.get("AZURE_BLOB_CONNECTION_STRING")
    res = await self.db.run("db:system:config:get_config:1", {"key": "AzureBlobContainerName"})
    if not res.rows:
      raise ValueError("Missing config value for key: AzureBlobContainerName")
    self.container = res.rows[0]["value"]
    logging.debug("[StorageModule] Using container %s", self.container)

    bsc = BlobServiceClient.from_connection_string(dsn)
    self.client = bsc.get_container_client(self.container)
    try:
      logging.debug("[StorageModule] Attempting to create container %s", self.container)
      await self.client.create_container()
    except ResourceExistsError:
      logging.debug("[StorageModule] Container %s already exists", self.container)
    logging.info("Storage module loaded container %s", self.container)

    self.mark_ready()

  async def shutdown(self):
    if self.client:
      await self.client.close()
      self.client = None
    logging.info("Storage module shutdown")

  async def write_buffer(self, buffer: io.BytesIO, user_guid: str, filename: str, content_type: str | None = None):
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    logging.debug("[StorageModule] write_buffer user=%s filename=%s ct=%s", user_guid, filename, content_type)
    safe = filename.replace(" ", "_")
    buffer.seek(0)
    blob_name = f"{user_guid}/{safe}"
    kwargs = {"data": buffer, "name": blob_name, "overwrite": True}
    if content_type:
      from azure.storage.blob import ContentSettings
      kwargs["content_settings"] = ContentSettings(content_type=content_type)
    try:
      await self.client.upload_blob(**kwargs)
      logging.info("Uploaded blob %s", blob_name)
    except Exception as e:
      logging.error("[StorageModule] Failed to upload blob %s: %s", blob_name, e)
      raise

  async def user_folder_exists(self, user_guid: str) -> bool:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
    logging.debug("[StorageModule] Checking folder existence prefix=%s", prefix)
    async for _ in self.client.list_blobs(name_starts_with=prefix):
      logging.debug("[StorageModule] Folder exists for %s", user_guid)
      return True
    logging.debug("[StorageModule] Folder does not exist for %s", user_guid)
    return False

  async def get_user_folder_size(self, user_guid: str) -> int:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
    logging.debug("[StorageModule] Calculating folder size prefix=%s", prefix)
    size = 0
    async for blob in self.client.list_blobs(name_starts_with=prefix):
      try:
        size += blob.size
      except AttributeError:
        sz = getattr(blob, "get", lambda k: None)("size")
        size += sz if sz else 0
    logging.debug("[StorageModule] Folder size for %s: %d", user_guid, size)
    return size

  async def ensure_user_folder(self, user_guid: str) -> None:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    logging.debug("[StorageModule] Ensuring folder for %s", user_guid)
    if await self.user_folder_exists(user_guid):
      logging.debug("[StorageModule] Folder already exists for %s", user_guid)
      return
    data = io.BytesIO(b"")
    await self.client.upload_blob(
      data=data,
      name=f"{user_guid}/.init",
      overwrite=True,
    )
    logging.info("Initialized storage folder for %s", user_guid)

  async def create_folder(self, user_guid: str, folder_path: str) -> None:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    await self.ensure_user_folder(user_guid)
    safe = folder_path.strip("/").replace(" ", "_")
    data = io.BytesIO(b"")
    name = f"{user_guid}/{safe}/.init"
    await self.client.upload_blob(
      data=data,
      name=name,
      overwrite=True,
    )
    logging.info("Created folder %s for %s", folder_path, user_guid)

  async def list_user_files(self, user_guid: str) -> list[dict[str, str | None]]:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
    logging.debug("[StorageModule] Listing files with prefix=%s", prefix)
    files: list[dict[str, str | None]] = []
    async for blob in self.client.list_blobs(name_starts_with=prefix):
      name = getattr(blob, "name", getattr(blob, "get", lambda k: None)("name"))
      if not name or name == f"{user_guid}/.init":
        continue
      short = name[len(prefix):]
      ct = None
      if hasattr(blob, "content_type"):
        ct = blob.content_type
      elif hasattr(blob, "content_settings"):
        ct = getattr(blob.content_settings, "content_type", None)
      url = f"{self.client.url}/{name}"
      files.append({"name": short, "url": url, "content_type": ct})
    logging.debug("[StorageModule] Found %d files for %s", len(files), user_guid)
    return files

  async def delete_user_file(self, user_guid: str, filename: str) -> None:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    name = f"{user_guid}/{filename}"
    logging.debug("[StorageModule] Deleting blob %s", name)
    try:
      await self.client.delete_blob(name)
      logging.info("Deleted blob %s", name)
    except Exception as e:
      logging.error("[StorageModule] Failed to delete blob %s: %s", name, e)
      raise


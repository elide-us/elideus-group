from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvModule
from .mssql_module import MSSQLModule
import io, logging

class StorageModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.client: ContainerClient = None
    self.container = ""

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.mssql: MSSQLModule = self.app.state.mssql
    await self.mssql.on_ready()

    dsn = self.env.get("AZURE_BLOB_CONNECTION_STRING")
    self.container = await self.mssql.get_config_value("AzureBlobContainerName")

    bsc = BlobServiceClient.from_connection_string(dsn)
    self.client = bsc.get_container_client(self.container)
    try:
      await self.client.create_container()
    except ResourceExistsError:
      pass
    logging.info("Storage module loaded container %s", self.container)

    self.mark_ready()

  async def shutdown(self):
    self.client = None
    logging.info("Storage module shutdown")

  async def write_buffer(self, buffer: io.BytesIO, user_guid: str, filename: str, content_type: str | None = None):
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    safe = filename.replace(" ", "_")
    buffer.seek(0)
    blob_name = f"{user_guid}/{safe}"
    kwargs = {"data": buffer, "name": blob_name, "overwrite": True}
    if content_type:
      from azure.storage.blob import ContentSettings
      kwargs["content_settings"] = ContentSettings(content_type=content_type)
    await self.client.upload_blob(**kwargs)
    logging.info("Uploaded blob %s", blob_name)

  async def user_folder_exists(self, user_guid: str) -> bool:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
    logging.debug("Checking folder existence for %s", user_guid)
    async for _ in self.client.list_blobs(name_starts_with=prefix):
      return True
    return False

  async def get_user_folder_size(self, user_guid: str) -> int:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
    logging.debug("Calculating folder size for %s", user_guid)
    size = 0
    async for blob in self.client.list_blobs(name_starts_with=prefix):
      try:
        size += blob.size
      except AttributeError:
        sz = getattr(blob, "get", lambda k: None)("size")
        size += sz if sz else 0
    return size

  async def ensure_user_folder(self, user_guid: str) -> None:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    if await self.user_folder_exists(user_guid):
      return
    data = io.BytesIO(b"")
    await self.client.upload_blob(
      data=data,
      name=f"{user_guid}/.init",
      overwrite=True,
    )
    logging.info("Initialized storage folder for %s", user_guid)

  async def list_user_files(self, user_guid: str) -> list[dict[str, str | None]]:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    prefix = f"{user_guid}/"
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
    return files

  async def delete_user_file(self, user_guid: str, filename: str) -> None:
    if not self.client:
      raise RuntimeError("Storage client not initialized")
    name = f"{user_guid}/{filename}"
    await self.client.delete_blob(name)
    logging.info("Deleted blob %s", name)


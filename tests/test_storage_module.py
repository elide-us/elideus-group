import asyncio, io
from fastapi import FastAPI
import server.modules.storage_module as storage_mod
from server.modules.storage_module import StorageModule
from server.modules.env_module import EnvironmentModule

class DummyContainerClient:
  def __init__(self):
    self.created = False
    self.uploaded = []
    self.container_name = ""
  async def create_container(self):
    self.created = True
  async def upload_blob(self, data, name, overwrite=False):
    self.uploaded.append((name, data.read()))
  def list_blobs(self, name_starts_with=""):
    async def gen():
      for name, data in self.uploaded:
        if name.startswith(name_starts_with):
          class Blob:
            def __init__(self, size):
              self.size = size
          yield Blob(len(data))
    return gen()

class DummyBSC:
  def __init__(self, client):
    self.client = client
  def get_container_client(self, name):
    self.client.container_name = name
    return self.client


def _make_app(monkeypatch):
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  class DB:
    async def get_config_value(self, key):
      if key == "AzureBlobContainerName":
        return "elideus-group"
      return None
  app.state.database = DB()
  return app


def test_storage_startup_and_write(monkeypatch):
  app = _make_app(monkeypatch)
  container = DummyContainerClient()
  monkeypatch.setattr(
    storage_mod.BlobServiceClient,
    "from_connection_string",
    lambda cs: DummyBSC(container),
  )
  sm = StorageModule(app)
  asyncio.run(sm.startup())
  assert sm.container == "elideus-group"
  assert container.created
  buf = io.BytesIO(b"data")
  asyncio.run(sm.write_buffer(buf, "uid", "file.txt"))
  assert container.uploaded == [("uid/file.txt", b"data")]


def test_folder_exists_and_size(monkeypatch):
  app = _make_app(monkeypatch)
  container = DummyContainerClient()
  container.uploaded.append(("uid/file.txt", b"data"))
  monkeypatch.setattr(
    storage_mod.BlobServiceClient,
    "from_connection_string",
    lambda cs: DummyBSC(container),
  )
  sm = StorageModule(app)
  asyncio.run(sm.startup())
  exists = asyncio.run(sm.user_folder_exists("uid"))
  size = asyncio.run(sm.get_user_folder_size("uid"))
  assert exists
  assert size == 4


def test_ensure_user_folder(monkeypatch):
  app = _make_app(monkeypatch)
  container = DummyContainerClient()
  monkeypatch.setattr(
    storage_mod.BlobServiceClient,
    "from_connection_string",
    lambda cs: DummyBSC(container),
  )
  sm = StorageModule(app)
  asyncio.run(sm.startup())
  exists = asyncio.run(sm.user_folder_exists("uid"))
  assert not exists
  asyncio.run(sm.ensure_user_folder("uid"))
  assert container.uploaded == [("uid/.init", b"")]


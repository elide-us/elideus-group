import asyncio, io
from fastapi import FastAPI
import server.modules.storage_module as storage_mod
from server.modules.storage_module import StorageModule
from server.modules.env_module import EnvironmentModule

class DummyContainerClient:
  def __init__(self):
    self.created = False
    self.uploaded = []
    self.deleted = []
    self.container_name = ""
    self.url = "https://example.com/container"
  async def create_container(self):
    self.created = True
  async def upload_blob(self, data, name, overwrite=False):
    self.uploaded.append((name, data.read()))
  async def delete_blob(self, name):
    self.deleted.append(name)
    self.uploaded = [p for p in self.uploaded if p[0] != name]
  def list_blobs(self, name_starts_with=""):
    async def gen():
      for name, data in self.uploaded:
        if name.startswith(name_starts_with):
          class Blob:
            def __init__(self, n, d):
              self.name = n
              self.size = len(d)
              self.content_type = "text/plain"
              class CS:
                def __init__(self, ct):
                  self.content_type = ct
              self.content_settings = CS("text/plain")
          yield Blob(name, data)
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
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  class DB:
    async def get_config_value(self, key):
      if key == "AzureBlobContainerName":
        return "elideus-group"
      return None
  app.state.mssql = DB()
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


def test_list_and_delete_files(monkeypatch):
  app = _make_app(monkeypatch)
  container = DummyContainerClient()
  container.uploaded.append(("uid/file1.txt", b"one"))
  container.uploaded.append(("uid/file2.jpg", b"two"))
  monkeypatch.setattr(
    storage_mod.BlobServiceClient,
    "from_connection_string",
    lambda cs: DummyBSC(container),
  )
  sm = StorageModule(app)
  asyncio.run(sm.startup())
  files = asyncio.run(sm.list_user_files("uid"))
  assert len(files) == 2
  assert files[0]["name"] == "file1.txt"
  asyncio.run(sm.delete_user_file("uid", "file1.txt"))
  files = asyncio.run(sm.list_user_files("uid"))
  assert len(files) == 1
  assert files[0]["name"] == "file2.jpg"


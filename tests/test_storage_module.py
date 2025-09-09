import asyncio
from fastapi import FastAPI

from server.modules.storage_module import StorageModule
import server.modules.storage_module as storage_module
from server.modules import BaseModule


class DummyEnv(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._env = {"AZURE_BLOB_CONNECTION_STRING": "UseDevelopmentStorage=true"}

  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

  def get(self, key: str):
    return self._env.get(key)


class DummyDb(BaseModule):
  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

  async def run(self, op, args):
    class Res:
      def __init__(self, rows):
        self.rows = rows
    if op == "db:system:config:get_config:1" and args.get("key") == "StorageCacheTime":
      return Res([{ "value": "15m" }])
    return Res([])


class DummyListDb:
  def __init__(self, rows):
    self.rows = rows

  async def list_storage_cache(self, user_guid):
    return self.rows


def test_storage_module_startup_loads_connection_string_and_interval():
  app = FastAPI()
  app.state.env = DummyEnv(app)
  app.state.db = DummyDb(app)
  asyncio.run(app.state.env.startup())
  asyncio.run(app.state.db.startup())

  mod = StorageModule(app)
  asyncio.run(mod.startup())
  assert mod.connection_string == "UseDevelopmentStorage=true"
  assert mod.reindex_interval == 15 * 60


def test_parse_duration_shorthand():
  assert StorageModule._parse_duration("10m") == 600
  assert StorageModule._parse_duration("1d") == 86400
  assert StorageModule._parse_duration("2w") == 1209600


def test_list_files_by_user():
  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyListDb([
    {"path": "", "filename": "a.txt", "content_type": "text/plain", "url": "u/a.txt"},
    {"path": "docs", "filename": "b.txt", "content_type": "text/plain", "url": "u/docs/b.txt"},
    {"path": "", "filename": "docs", "content_type": "path/folder", "url": None},
  ])
  files = asyncio.run(mod.list_files_by_user("u1"))
  assert files == [
    {"name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"},
    {"name": "docs/b.txt", "url": "u/docs/b.txt", "content_type": "text/plain"},
  ]


def test_list_folder_returns_files_and_folders():
  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyListDb([
    {"path": "", "filename": "a.txt", "content_type": "text/plain", "url": "u/a.txt"},
    {"path": "", "filename": "docs", "content_type": "path/folder", "url": None},
    {"path": "", "filename": "empty", "content_type": "path/folder", "url": None},
    {"path": "docs", "filename": "b.txt", "content_type": "text/plain", "url": "u/docs/b.txt"},
    {"path": "docs", "filename": "c.txt", "content_type": "text/plain", "url": "u/docs/c.txt"},
    {"path": "docs", "filename": "sub", "content_type": "path/folder", "url": None},
    {"path": "docs/sub", "filename": "d.txt", "content_type": "text/plain", "url": "u/docs/sub/d.txt"},
  ])
  root = asyncio.run(mod.list_folder("u1", ""))
  assert root["path"] == ""
  assert root["files"] == [
    {"name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"}
  ]
  assert sorted(root["folders"], key=lambda x: x["name"]) == [
    {"name": "docs", "empty": False},
    {"name": "empty", "empty": True},
  ]
  docs = asyncio.run(mod.list_folder("u1", "/docs"))
  assert docs["path"] == "docs"
  assert docs["files"] == [
    {"name": "docs/b.txt", "url": "u/docs/b.txt", "content_type": "text/plain"},
    {"name": "docs/c.txt", "url": "u/docs/c.txt", "content_type": "text/plain"},
  ]
  assert docs["folders"] == [{"name": "sub", "empty": False}]


def test_reindex_indexes_files_and_folders(monkeypatch):
  class DummyEnv(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
    async def startup(self):
      self.mark_ready()
    def get(self, key: str):
      return "UseDevelopmentStorage=true"
    async def shutdown(self):
      pass

  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.upserts = []
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args):
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])
    async def upsert_storage_cache(self, item):
      self.upserts.append(item)
    async def list_storage_cache(self, user_guid):
      return []
    async def shutdown(self):
      pass

  app = FastAPI()
  app.state.env = DummyEnv(app)
  app.state.db = DummyDb(app)
  asyncio.run(app.state.env.startup())
  asyncio.run(app.state.db.startup())
  mod = StorageModule(app)
  mod.env = app.state.env
  mod.db = app.state.db
  mod.connection_string = "UseDevelopmentStorage=true"

  from types import SimpleNamespace

  class FakeBlob:
    def __init__(self, name):
      self.name = name
      self.content_settings = SimpleNamespace(content_type = "text/plain")
      self.creation_time = None
      self.last_modified = None

  class FakeContainer:
    def __init__(self, blobs):
      self.blobs = blobs
      self.url = "http://blob"
    def list_blobs(self, name_starts_with=None):
      async def gen():
        for b in self.blobs:
          if not name_starts_with or b.name.startswith(name_starts_with):
            yield b
      return gen()
    async def close(self):
      pass

  fake_container = FakeContainer([
    FakeBlob("123e4567-e89b-12d3-a456-426614174000/docs/.init"),
    FakeBlob("123e4567-e89b-12d3-a456-426614174000/docs/file.txt"),
  ])

  class FakeBSC:
    def get_container_client(self, name):
      return fake_container
    async def close(self):
      pass

  monkeypatch.setattr(
    storage_module,
    "BlobServiceClient",
    SimpleNamespace(from_connection_string=lambda conn: FakeBSC()),
  )

  asyncio.run(mod.reindex())
  assert any(u["filename"] == "docs" for u in app.state.db.upserts)
  assert any(u["filename"] == "file.txt" and u["path"] == "docs" for u in app.state.db.upserts)

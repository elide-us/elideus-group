import asyncio, base64
from datetime import datetime, timezone
from fastapi import FastAPI

from server.modules.storage_module import StorageModule
import server.modules.storage_module as storage_module
from server.modules import BaseModule
from server.modules.providers.database.mssql_provider import MssqlProvider
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers import DBResult


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


def test_list_public_files(monkeypatch):
  app = FastAPI()
  provider = MssqlProvider()

  async def fake_fetch_rows(sql, params, *, one=False, stream=False):
    assert not one
    return DBResult(rows=[
      {"user_guid": "u1", "display_name": "U1", "path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"},
      {"user_guid": "u2", "display_name": "U2", "path": "", "name": "b.txt", "url": "u/b.txt", "content_type": "text/plain"},
    ], rowcount=2)

  monkeypatch.setattr(mssql_provider, "fetch_rows", fake_fetch_rows)

  mod = StorageModule(app)
  mod.db = provider
  rows = asyncio.run(mod.list_public_files())
  assert rows == [
    {"user_guid": "u1", "display_name": "U1", "path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"},
    {"user_guid": "u2", "display_name": "U2", "path": "", "name": "b.txt", "url": "u/b.txt", "content_type": "text/plain"},
  ]


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
    {"path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"},
    {"path": "docs", "name": "b.txt", "url": "u/docs/b.txt", "content_type": "text/plain"},
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
    {"path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"}
  ]
  assert sorted(root["folders"], key=lambda x: x["name"]) == [
    {"name": "docs", "empty": False},
    {"name": "empty", "empty": True},
  ]
  docs = asyncio.run(mod.list_folder("u1", "/docs"))
  assert docs["path"] == "docs"
  assert docs["files"] == [
    {"path": "docs", "name": "b.txt", "url": "u/docs/b.txt", "content_type": "text/plain"},
    {"path": "docs", "name": "c.txt", "url": "u/docs/c.txt", "content_type": "text/plain"},
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
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)
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
    def __init__(self, name, metadata=None):
      self.name = name
      self.content_settings = SimpleNamespace(content_type = "text/plain")
      self.creation_time = None
      self.last_modified = None
      self.metadata = metadata

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
    FakeBlob("123e4567-e89b-12d3-a456-426614174000/empty_test", {"hdi_isfolder": "true"}),
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
  assert any(u["filename"] == "empty_test" and u["content_type"] == "path/folder" for u in app.state.db.upserts)


def test_move_file_copies_and_updates_cache(monkeypatch):
  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.deleted = None
      self.upserted = None
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args):
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])
    async def delete_storage_cache(self, user_guid, path, filename):
      self.deleted = (user_guid, path, filename)
    async def upsert_storage_cache(self, item):
      self.upserted = item
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)
    async def shutdown(self):
      pass

  app = FastAPI()
  db = DummyDb(app)
  asyncio.run(db.startup())
  mod = StorageModule(app)
  mod.db = db
  mod.connection_string = "UseDevelopmentStorage=true"

  from types import SimpleNamespace

  class FakeBlob:
    def __init__(self, name):
      self.name = name
      self.url = f"http://blob/{name}"
      self.copied = None
      self.deleted = False
      self.content_settings = SimpleNamespace(content_type="text/plain")
      self.creation_time = "now"
      self.last_modified = "later"
    async def get_blob_properties(self):
      return self
    async def start_copy_from_url(self, url):
      self.copied = url
    async def delete_blob(self):
      self.deleted = True

  blobs = {
    "u1/a.txt": FakeBlob("u1/a.txt"),
    "u1/docs/b.txt": FakeBlob("u1/docs/b.txt"),
  }

  class FakeContainer:
    def get_blob_client(self, name):
      return blobs[name]
    async def close(self):
      pass

  fake_container = FakeContainer()

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

  asyncio.run(mod.move_file("u1", "a.txt", "docs/b.txt"))
  assert blobs["u1/docs/b.txt"].copied == blobs["u1/a.txt"].url
  assert blobs["u1/a.txt"].deleted
  assert db.deleted == ("u1", "", "a.txt")
  assert db.upserted["path"] == "docs" and db.upserted["filename"] == "b.txt"


def test_get_storage_stats_counts_all_folders(monkeypatch):
  class DummyDb:
    async def run(self, op, args):
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:storage:cache:count_rows:1":
        return Res([{ "count": 10 }])
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyDb()
  mod.connection_string = "UseDevelopmentStorage=true"

  from types import SimpleNamespace

  class FakeBlob:
    def __init__(self, name, size):
      self.name = name
      self.size = size

  class FakeContainer:
    def __init__(self, blobs):
      self.blobs = blobs
      self.url = "http://blob"
    def list_blobs(self):
      async def gen():
        for b in self.blobs:
          yield b
      return gen()
    async def close(self):
      pass

  fake_container = FakeContainer([
    FakeBlob("123e4567-e89b-12d3-a456-426614174000/docs/file1.txt", 1),
    FakeBlob("123e4567-e89b-12d3-a456-426614174000/docs/sub/file2.txt", 2),
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

  stats = asyncio.run(mod.get_storage_stats())
  assert stats == {
    "file_count": 2,
    "total_bytes": 3,
    "folder_count": 2,
    "user_folder_count": 1,
    "db_rows": 10,
  }


def test_upload_files_sets_created_on(monkeypatch):
  app = FastAPI()
  mod = StorageModule(app)
  mod.connection_string = "UseDevelopmentStorage=true"

  class DummyDb:
    def __init__(self):
      self.upserts = []

    async def run(self, op, args):
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

    async def upsert_storage_cache(self, data):
      self.upserts.append(data)
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)

  mod.db = DummyDb()

  class FakeContainer:
    def __init__(self):
      self.uploads = []
      self.url = "http://blob"

    async def upload_blob(self, name, data, overwrite, content_settings=None):
      self.uploads.append((name, data, getattr(content_settings, "content_type", None)))

    async def close(self):
      pass

  fake_container = FakeContainer()

  class FakeBSC:
    def get_container_client(self, name):
      return fake_container

    async def close(self):
      pass

  from types import SimpleNamespace

  monkeypatch.setattr(
    storage_module,
    "BlobServiceClient",
    SimpleNamespace(from_connection_string=lambda conn: FakeBSC()),
  )

  files = [{
    "name": "docs/a.txt",
    "content_b64": base64.b64encode(b"hello").decode(),
    "content_type": "text/plain",
  }]

  asyncio.run(mod.upload_files("u1", files))

  assert fake_container.uploads[0][0] == "u1/docs/a.txt"
  created_on = mod.db.upserts[0]["created_on"]
  assert isinstance(created_on, datetime)
  assert created_on.tzinfo == timezone.utc


def test_create_folder_creates_marker_and_cache(monkeypatch):
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
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)
    async def list_storage_cache(self, user_guid):
      return []
    async def shutdown(self):
      pass

  class DummyEnv(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
    async def startup(self):
      self.mark_ready()
    def get(self, key: str):
      return "UseDevelopmentStorage=true"
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

  class FakeContainer:
    def __init__(self):
      self.uploads = []
    async def upload_blob(self, name, data, **kwargs):
      self.uploads.append((name, kwargs.get("metadata")))
    async def close(self):
      pass

  class FakeBSC:
    def __init__(self):
      self.container = FakeContainer()
    def get_container_client(self, name):
      return self.container
    async def close(self):
      pass

  from types import SimpleNamespace
  bsc = FakeBSC()
  monkeypatch.setattr(
    storage_module,
    "BlobServiceClient",
    SimpleNamespace(from_connection_string=lambda conn: bsc),
  )

  asyncio.run(mod.create_folder("u1", "/docs/new"))
  assert ("u1/docs/new", {"hdi_isfolder": "true"}) in bsc.container.uploads
  assert ("u1/docs/new/.init", None) in bsc.container.uploads
  assert app.state.db.upserts[0]["filename"] == "new"
  assert app.state.db.upserts[0]["path"] == "docs"
  assert app.state.db.upserts[0]["content_type"] == "path/folder"


def test_get_storage_stats_counts_user_folders(monkeypatch):
  class DummyDb:
    async def run(self, op, args):
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:storage:cache:count_rows:1":
        return Res([{ "count": 0 }])
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyDb()
  mod.connection_string = "UseDevelopmentStorage=true"

  class FakeBlob:
    def __init__(self, name, size=0):
      self.name = name
      self.size = size

  blobs = [
    FakeBlob("11111111-1111-1111-1111-111111111111/file.txt", 1),
    FakeBlob("22222222-2222-2222-2222-222222222222/docs/a.txt", 1),
    FakeBlob("33333333-3333-3333-3333-333333333333/docs/sub/b.txt", 1),
    FakeBlob("44444444-4444-4444-4444-444444444444/.init", 0),
    FakeBlob("notguid/skip.txt", 1),
  ]

  class FakeContainer:
    def __init__(self):
      self.url = "http://blob"
    def list_blobs(self):
      async def gen():
        for b in blobs:
          yield b
      return gen()
    async def close(self):
      pass

  class FakeBSC:
    def __init__(self):
      self.container = FakeContainer()
    def get_container_client(self, name):
      return self.container
    async def close(self):
      pass

  from types import SimpleNamespace
  monkeypatch.setattr(
    storage_module,
    "BlobServiceClient",
    SimpleNamespace(from_connection_string=lambda conn: FakeBSC()),
  )

  stats = asyncio.run(mod.get_storage_stats())
  assert stats == {
    "file_count": 3,
    "total_bytes": 3,
    "folder_count": 3,
    "user_folder_count": 4,
    "db_rows": 0,
  }

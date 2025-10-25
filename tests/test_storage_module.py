import asyncio, base64
from datetime import datetime, timezone
from fastapi import FastAPI

from server.modules.storage_module import StorageModule
import server.modules.storage_module as storage_module
from server.modules import BaseModule
from server.modules.providers.database.mssql_provider import MssqlProvider
import server.registry.providers.mssql as registry_mssql
from server.modules.providers import DBResult
from server.modules.providers.storage import (
  StorageBlobItem,
  StorageBlobProperties,
  StorageCreateFolderResult,
  StorageDeleteResponse,
  StorageMoveResult,
  StorageRenameOperation,
  StorageRenameResponse,
  StorageReindexResponse,
  StorageStats,
  StorageUploadResult,
  StorageUploadResponse,
)


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

  async def run(self, op, args=None):
    if not isinstance(op, str):
      args = op.payload
      op = op.op
    elif args is None:
      args = {}
    class Res:
      def __init__(self, rows):
        self.rows = rows
    if op == "db:system:config:get_config:1" and args.get("key") == "StorageCacheTime":
      return Res([{ "value": "15m" }])
    return Res([])

  async def user_exists(self, user_guid):
    return True


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

  async def fake_fetch_json(sql, params, *, many=False):
    assert many
    return DBResult(rows=[
      {"user_guid": "u1", "display_name": "U1", "path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"},
      {"user_guid": "u2", "display_name": "U2", "path": "", "name": "b.txt", "url": "u/b.txt", "content_type": "text/plain"},
    ], rowcount=2)

  monkeypatch.setattr(registry_mssql, "fetch_json", fake_fetch_json)

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
    {"path": "", "filename": "a.txt", "content_type": "text/plain", "url": "u/a.txt", "public": 0},
    {"path": "docs", "filename": "b.txt", "content_type": "text/plain", "url": "u/docs/b.txt", "public": 0},
    {"path": "", "filename": "docs", "content_type": "path/folder", "url": None},
  ])
  files = asyncio.run(mod.list_files_by_user("u1"))
  assert files == [
    {"path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain", "gallery": False},
    {"path": "docs", "name": "b.txt", "url": "u/docs/b.txt", "content_type": "text/plain", "gallery": False},
  ]


def test_list_folder_returns_files_and_folders():
  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyListDb([
    {"path": "", "filename": "a.txt", "content_type": "text/plain", "url": "u/a.txt", "public": 0},
    {"path": "", "filename": "docs", "content_type": "path/folder", "url": None, "public": 0},
    {"path": "", "filename": "empty", "content_type": "path/folder", "url": None, "public": 0},
    {"path": "docs", "filename": "b.txt", "content_type": "text/plain", "url": "u/docs/b.txt", "public": 0},
    {"path": "docs", "filename": "c.txt", "content_type": "text/plain", "url": "u/docs/c.txt", "public": 0},
    {"path": "docs", "filename": "sub", "content_type": "path/folder", "url": None, "public": 0},
    {"path": "docs/sub", "filename": "d.txt", "content_type": "text/plain", "url": "u/docs/sub/d.txt", "public": 0},
  ])
  root = asyncio.run(mod.list_folder("u1", ""))
  assert root["path"] == ""
  assert root["files"] == [
    {"path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain", "gallery": False}
  ]
  assert sorted(root["folders"], key=lambda x: x["name"]) == [
    {"name": "docs", "empty": False},
    {"name": "empty", "empty": True},
  ]
  docs = asyncio.run(mod.list_folder("u1", "/docs"))
  assert docs["path"] == "docs"
  assert docs["files"] == [
    {"path": "docs", "name": "b.txt", "url": "u/docs/b.txt", "content_type": "text/plain", "gallery": False},
    {"path": "docs", "name": "c.txt", "url": "u/docs/c.txt", "content_type": "text/plain", "gallery": False},
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
      self.existing = set()
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
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
    async def user_exists(self, user_guid):
      if not self.existing:
        return True
      return user_guid in self.existing
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

  class FakeProvider:
    async def reindex(self, request):
      return StorageReindexResponse(
        container_url="http://blob",
        blobs=[
          StorageBlobItem(
            name="123e4567-e89b-12d3-a456-426614174000/docs/.init",
            metadata={},
            content_type="text/plain",
            created_on=None,
            modified_on=None,
            url="http://blob/123e4567-e89b-12d3-a456-426614174000/docs/.init",
            size=None,
            is_directory=False,
          ),
          StorageBlobItem(
            name="123e4567-e89b-12d3-a456-426614174000/docs/file.txt",
            metadata={},
            content_type="text/plain",
            created_on=None,
            modified_on=None,
            url="http://blob/123e4567-e89b-12d3-a456-426614174000/docs/file.txt",
            size=None,
            is_directory=False,
          ),
          StorageBlobItem(
            name="123e4567-e89b-12d3-a456-426614174000/empty_test",
            metadata={"hdi_isfolder": "true"},
            content_type="text/plain",
            created_on=None,
            modified_on=None,
            url="http://blob/123e4567-e89b-12d3-a456-426614174000/empty_test",
            size=None,
            is_directory=True,
          ),
        ],
      )

  mod.provider = FakeProvider()

  asyncio.run(mod.reindex())
  assert any(u["filename"] == "docs" for u in app.state.db.upserts)
  assert any(u["filename"] == "file.txt" and u["path"] == "docs" for u in app.state.db.upserts)
  assert any(u["filename"] == "empty_test" and u["content_type"] == "path/folder" for u in app.state.db.upserts)


def test_reindex_skips_unknown_users(monkeypatch):
  known_guid = "123e4567-e89b-12d3-a456-426614174000"
  orphan_guid = "11111111-1111-1111-1111-111111111111"

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
      self.checked = []
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
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
    async def user_exists(self, user_guid):
      self.checked.append(user_guid)
      return user_guid == known_guid
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

  class FakeProvider:
    async def reindex(self, request):
      return StorageReindexResponse(
        container_url="http://blob",
        blobs=[
          StorageBlobItem(
            name=f"{orphan_guid}/docs/file.txt",
            metadata={},
            content_type="text/plain",
            created_on=None,
            modified_on=None,
            url=f"http://blob/{orphan_guid}/docs/file.txt",
            size=None,
            is_directory=False,
          ),
          StorageBlobItem(
            name=f"{known_guid}/docs/file.txt",
            metadata={},
            content_type="text/plain",
            created_on=None,
            modified_on=None,
            url=f"http://blob/{known_guid}/docs/file.txt",
            size=None,
            is_directory=False,
          ),
        ],
      )

  mod.provider = FakeProvider()

  asyncio.run(mod.reindex())
  assert app.state.db.upserts
  assert all(item["user_guid"] == known_guid for item in app.state.db.upserts)
  assert orphan_guid in app.state.db.checked
  assert known_guid in app.state.db.checked


def test_move_file_copies_and_updates_cache(monkeypatch):
  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.deleted = None
      self.upserted = None
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
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

  class FakeProvider:
    def __init__(self):
      self.requests = []

    async def move_file(self, request):
      self.requests.append(request)
      return StorageMoveResult(
        src_relative=request.src_relative,
        dst_relative=request.dst_relative,
        url=f"http://blob/{request.dst_blob}",
        properties=StorageBlobProperties(
          content_type="text/plain",
          created_on="now",
          modified_on="later",
        ),
      )

  provider = FakeProvider()
  mod.provider = provider

  asyncio.run(mod.move_file("u1", "a.txt", "docs/b.txt"))
  assert provider.requests
  request = provider.requests[0]
  assert request.src_blob == "u1/a.txt"
  assert request.dst_blob == "u1/docs/b.txt"
  assert db.deleted == ("u1", "", "a.txt")
  assert db.upserted["path"] == "docs" and db.upserted["filename"] == "b.txt"


def test_rename_file_preserves_public_flag():
  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.deleted = []
      self.upserted = []

    async def startup(self):
      self.mark_ready()

    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

    async def delete_storage_cache(self, user_guid, path, filename):
      self.deleted.append((user_guid, path, filename))

    async def upsert_storage_cache(self, item):
      self.upserted.append(item)
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)

    async def list_storage_cache(self, user_guid):
      return [{
        "path": "",
        "filename": "a.txt",
        "content_type": "text/plain",
        "public": 1,
        "created_on": "old",
        "modified_on": "old",
        "url": "http://blob/container/u1/a.txt",
        "reported": 0,
        "moderation_recid": None,
      }]

    async def shutdown(self):
      pass

  app = FastAPI()
  db = DummyDb(app)
  asyncio.run(db.startup())
  mod = StorageModule(app)
  mod.db = db
  mod.connection_string = "UseDevelopmentStorage=true"
  class FakeProvider:
    def __init__(self):
      self.requests = []

    async def rename_file(self, request):
      self.requests.append(request)
      return StorageRenameResponse(
        container_url="http://blob/container",
        operations=[
          StorageRenameOperation(
            old_relative="a.txt",
            new_relative="b.txt",
            url="http://blob/container/u1/b.txt",
            properties=StorageBlobProperties(
              content_type="text/plain",
              created_on="now",
              modified_on="later",
            ),
            source_missing=False,
          ),
        ],
        errors=[],
      )

  provider = FakeProvider()
  mod.provider = provider

  asyncio.run(mod.rename_file("u1", "a.txt", "b.txt"))
  assert provider.requests and not provider.requests[0].is_folder
  assert ("u1", "", "a.txt") in db.deleted
  assert any(item["filename"] == "b.txt" and item["public"] == 1 for item in db.upserted)


def test_rename_folder_updates_nested_entries():
  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.deleted = []
      self.upserted = []

    async def startup(self):
      self.mark_ready()

    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

    async def delete_storage_cache(self, user_guid, path, filename):
      self.deleted.append((user_guid, path, filename))

    async def upsert_storage_cache(self, item):
      self.upserted.append(item)
      from types import SimpleNamespace
      return SimpleNamespace(rowcount=1)

    async def list_storage_cache(self, user_guid):
      return [
        {"path": "", "filename": "docs", "content_type": "path/folder", "public": 0, "url": None, "created_on": None, "modified_on": None, "reported": 0, "moderation_recid": None},
        {"path": "docs", "filename": "a.txt", "content_type": "text/plain", "public": 1, "url": "http://blob/container/u1/docs/a.txt", "created_on": "old", "modified_on": "old", "reported": 0, "moderation_recid": None},
        {"path": "docs", "filename": "sub", "content_type": "path/folder", "public": 0, "url": None, "created_on": None, "modified_on": None, "reported": 0, "moderation_recid": None},
        {"path": "docs/sub", "filename": "b.txt", "content_type": "text/plain", "public": 0, "url": "http://blob/container/u1/docs/sub/b.txt", "created_on": "old", "modified_on": "old", "reported": 0, "moderation_recid": None},
      ]

    async def shutdown(self):
      pass

  app = FastAPI()
  db = DummyDb(app)
  asyncio.run(db.startup())
  mod = StorageModule(app)
  mod.db = db
  mod.connection_string = "UseDevelopmentStorage=true"
  class FakeProvider:
    def __init__(self):
      self.requests = []

    async def rename_file(self, request):
      self.requests.append(request)
      return StorageRenameResponse(
        container_url="http://blob/container",
        operations=[
          StorageRenameOperation(
            old_relative="docs",
            new_relative="renamed",
            url=None,
            properties=None,
            source_missing=False,
          ),
          StorageRenameOperation(
            old_relative="docs/a.txt",
            new_relative="renamed/a.txt",
            url="http://blob/container/u1/renamed/a.txt",
            properties=StorageBlobProperties(
              content_type="text/plain",
              created_on="now",
              modified_on="later",
            ),
            source_missing=False,
          ),
          StorageRenameOperation(
            old_relative="docs/sub",
            new_relative="renamed/sub",
            url=None,
            properties=None,
            source_missing=False,
          ),
          StorageRenameOperation(
            old_relative="docs/sub/b.txt",
            new_relative="renamed/sub/b.txt",
            url="http://blob/container/u1/renamed/sub/b.txt",
            properties=StorageBlobProperties(
              content_type="text/plain",
              created_on="now",
              modified_on="later",
            ),
            source_missing=False,
          ),
        ],
        errors=[],
      )

  provider = FakeProvider()
  mod.provider = provider

  asyncio.run(mod.rename_file("u1", "docs", "renamed"))
  assert provider.requests and provider.requests[0].is_folder
  assert any(item["filename"] == "renamed" for item in db.upserted)
  paths = {(item["path"], item["filename"]) for item in db.upserted}
  assert ("", "renamed") in paths
  assert ("renamed", "a.txt") in paths
  assert ("renamed", "sub") in paths
  assert ("renamed/sub", "b.txt") in paths

def test_get_storage_stats_counts_all_folders():
  class DummyDb:
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:account:cache:count_rows:1":
        return Res([{ "count": 10 }])
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyDb()
  mod.connection_string = "UseDevelopmentStorage=true"
  class FakeProvider:
    async def get_storage_stats(self, request):
      return StorageStats(
        file_count=2,
        total_bytes=3,
        folder_paths=[
          ("123e4567-e89b-12d3-a456-426614174000", "docs"),
          ("123e4567-e89b-12d3-a456-426614174000", "docs/sub"),
        ],
        user_ids=["123e4567-e89b-12d3-a456-426614174000"],
      )

  mod.provider = FakeProvider()

  stats = asyncio.run(mod.get_storage_stats())
  assert stats == {
    "file_count": 2,
    "total_bytes": 3,
    "folder_count": 2,
    "user_folder_count": 1,
    "db_rows": 10,
  }


def test_upload_files_sets_created_on():
  app = FastAPI()
  mod = StorageModule(app)
  mod.connection_string = "UseDevelopmentStorage=true"

  class DummyDb:
    def __init__(self):
      self.upserts = []

    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
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

  class FakeProvider:
    def __init__(self):
      self.requests = []

    async def upload_files(self, request):
      self.requests.append(request)
      now = datetime.now(timezone.utc)
      return StorageUploadResponse(
        results=[
          StorageUploadResult(
            relative_path="docs/a.txt",
            url="http://blob/u1/docs/a.txt",
            content_type="text/plain",
            created_on=now,
            modified_on=now,
          )
        ],
        errors={},
      )

  provider = FakeProvider()
  mod.provider = provider

  files = [{
    "name": "docs/a.txt",
    "content_b64": base64.b64encode(b"hello").decode(),
    "content_type": "text/plain",
  }]

  asyncio.run(mod.upload_files("u1", files))
  created_on = mod.db.upserts[0]["created_on"]
  assert isinstance(created_on, datetime)
  assert created_on.tzinfo == timezone.utc


def test_create_folder_creates_marker_and_cache():
  class DummyDb(BaseModule):
    def __init__(self, app: FastAPI):
      super().__init__(app)
      self.upserts = []
    async def startup(self):
      self.mark_ready()
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
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
  class FakeProvider:
    def __init__(self):
      self.requests = []

    async def create_folder(self, request):
      self.requests.append(request)
      return StorageCreateFolderResult(relative_path="docs/new")

  provider = FakeProvider()
  mod.provider = provider

  asyncio.run(mod.create_folder("u1", "/docs/new"))
  assert provider.requests
  assert app.state.db.upserts[0]["filename"] == "new"
  assert app.state.db.upserts[0]["path"] == "docs"
  assert app.state.db.upserts[0]["content_type"] == "path/folder"


def test_get_storage_stats_counts_user_folders():
  class DummyDb:
    async def run(self, op, args=None):
      if not isinstance(op, str):
        args = op.payload
        op = op.op
      elif args is None:
        args = {}
      class Res:
        def __init__(self, rows):
          self.rows = rows
      if op == "db:account:cache:count_rows:1":
        return Res([{ "count": 0 }])
      if op == "db:system:config:get_config:1" and args.get("key") == "AzureBlobContainerName":
        return Res([{ "value": "container" }])
      return Res([])

  app = FastAPI()
  mod = StorageModule(app)
  mod.db = DummyDb()
  mod.connection_string = "UseDevelopmentStorage=true"
  class FakeProvider:
    async def get_storage_stats(self, request):
      return StorageStats(
        file_count=3,
        total_bytes=3,
        folder_paths=[
          ("22222222-2222-2222-2222-222222222222", "docs"),
          ("33333333-3333-3333-3333-333333333333", "docs"),
          ("33333333-3333-3333-3333-333333333333", "docs/sub"),
        ],
        user_ids=[
          "11111111-1111-1111-1111-111111111111",
          "22222222-2222-2222-2222-222222222222",
          "33333333-3333-3333-3333-333333333333",
          "44444444-4444-4444-4444-444444444444",
        ],
      )

  mod.provider = FakeProvider()

  stats = asyncio.run(mod.get_storage_stats())
  assert stats == {
    "file_count": 3,
    "total_bytes": 3,
    "folder_count": 3,
    "user_folder_count": 4,
    "db_rows": 0,
  }

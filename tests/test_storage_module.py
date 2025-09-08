import asyncio
from fastapi import FastAPI

from server.modules.storage_module import StorageModule
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
    {"path": "docs", "filename": "b.txt", "content_type": "text/plain", "url": "u/docs/b.txt"},
    {"path": "docs", "filename": "c.txt", "content_type": "text/plain", "url": "u/docs/c.txt"},
    {"path": "docs/sub", "filename": "d.txt", "content_type": "text/plain", "url": "u/docs/sub/d.txt"},
  ])
  root = asyncio.run(mod.list_folder("u1", ""))
  assert root == {
    "path": "",
    "files": [{"name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"}],
    "folders": [{"name": "docs", "empty": False}],
  }
  docs = asyncio.run(mod.list_folder("u1", "/docs"))
  assert docs == {
    "path": "docs",
    "files": [
      {"name": "docs/b.txt", "url": "u/docs/b.txt", "content_type": "text/plain"},
      {"name": "docs/c.txt", "url": "u/docs/c.txt", "content_type": "text/plain"},
    ],
    "folders": [{"name": "sub", "empty": False}],
  }

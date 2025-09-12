import asyncio
import importlib.util
import pathlib
import types
import sys
from pydantic import BaseModel

# stub rpc package and helpers
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", rpc_pkg)

storage_pkg = types.ModuleType("rpc.storage")
storage_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc/storage")]
sys.modules.setdefault("rpc.storage", storage_pkg)

files_pkg = types.ModuleType("rpc.storage.files")
files_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc/storage/files")]
sys.modules.setdefault("rpc.storage.files", files_pkg)

models_spec = importlib.util.spec_from_file_location(
  "rpc.storage.files.models",
  pathlib.Path(__file__).resolve().parent.parent / "rpc/storage/files/models.py",
)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
sys.modules.setdefault("rpc.storage.files.models", models_module)

helpers_pkg = types.ModuleType("rpc.helpers")

async def unbox_request(request):
  return request.state.rpc_request, request.state.auth_ctx, []

helpers_pkg.unbox_request = unbox_request
sys.modules.setdefault("rpc.helpers", helpers_pkg)

# stub server models
server_pkg = types.ModuleType("server")
models_pkg = types.ModuleType("server.models")

class RPCRequest(BaseModel):
  op: str
  payload: dict | None = None
  version: int = 1


class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int = 1


class AuthContext(BaseModel):
  user_guid: str | None = None


models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg
sys.modules.setdefault("server", server_pkg)
sys.modules.setdefault("server.models", models_pkg)

# load services module
spec = importlib.util.spec_from_file_location(
  "rpc.storage.files.services",
  pathlib.Path(__file__).resolve().parent.parent / "rpc/storage/files/services.py",
)
services = importlib.util.module_from_spec(spec)
spec.loader.exec_module(services)

storage_files_get_link_v1 = services.storage_files_get_link_v1
storage_files_upload_files_v1 = services.storage_files_upload_files_v1
storage_files_delete_files_v1 = services.storage_files_delete_files_v1
storage_files_delete_folder_v1 = services.storage_files_delete_folder_v1
storage_files_rename_file_v1 = services.storage_files_rename_file_v1
storage_files_move_file_v1 = services.storage_files_move_file_v1
storage_files_get_metadata_v1 = services.storage_files_get_metadata_v1
storage_files_get_usage_v1 = services.storage_files_get_usage_v1
storage_files_get_folder_files_v1 = services.storage_files_get_folder_files_v1
storage_files_set_gallery_v1 = services.storage_files_set_gallery_v1
storage_files_get_public_files_v1 = services.storage_files_get_public_files_v1


class DummyStorage:
  def __init__(self):
    self.link_args = None
    self.upload_args = None
    self.deleted = None
    self.deleted_files = None
    self.reindexed = None
    self.renamed = None
    self.moved = None
    self.metadata_args = None
    self.usage_called = None
    self.list_folder_args = None
    self.gallery_args = None
    self.list_public_called = False

  async def get_file_link(self, user_guid, name):
    self.link_args = (user_guid, name)
    return f"https://example.com/{name}"

  async def upload_files(self, user_guid, files):
    self.upload_args = (user_guid, files)

  async def delete_files(self, user_guid, files):
    self.deleted_files = (user_guid, files)

  async def delete_folder(self, user_guid, path):
    self.deleted = (user_guid, path)

  async def reindex(self, user_guid=None):
    self.reindexed = user_guid

  async def rename_file(self, user_guid, old_name, new_name):
    self.renamed = (user_guid, old_name, new_name)

  async def move_file(self, user_guid, src, dst):
    self.moved = (user_guid, src, dst)

  async def get_file_metadata(self, user_guid, name):
    self.metadata_args = (user_guid, name)
    return {
      "name": name,
      "size": 1,
      "content_type": "text/plain",
      "created_on": "now",
      "modified_on": "now",
    }

  async def get_usage(self, user_guid):
    self.usage_called = user_guid
    return {
      "total_size": 10,
      "by_type": [{"content_type": "text/plain", "size": 10}],
    }

  async def list_folder(self, user_guid, path):
    self.list_folder_args = (user_guid, path)
    return {
      "path": path,
      "files": [{
        "path": path,
        "name": "a.txt",
        "url": f"u/{path}/a.txt",
        "content_type": "text/plain",
        "gallery": False,
      }],
      "folders": [{"name": "sub", "empty": False}],
    }

  async def set_gallery(self, user_guid, name, gallery):
    self.gallery_args = (user_guid, name, gallery)

  async def list_public_files(self):
    self.list_public_called = True
    return [
      {"path": "", "name": "a.txt", "url": "u/a.txt", "content_type": "text/plain"}
    ]


def make_request(op, payload):
  storage = DummyStorage()
  req = types.SimpleNamespace()
  req.app = types.SimpleNamespace(state=types.SimpleNamespace(storage=storage))
  req.state = types.SimpleNamespace(
    rpc_request=RPCRequest(op=op, payload=payload, version=1),
    auth_ctx=AuthContext(user_guid="u123"),
  )
  req.headers = {}
  return req, storage


def test_get_link_calls_storage():
  req, storage = make_request("urn:storage:files:get_link:1", {"name": "a.txt"})
  resp = asyncio.run(storage_files_get_link_v1(req))
  assert resp.payload == {
    "path": "",
    "name": "a.txt",
    "url": "https://example.com/a.txt",
    "content_type": None,
    "user_guid": None,
    "display_name": None,
    "gallery": None,
  }
  assert storage.link_args == ("u123", "a.txt")
  assert storage.reindexed == "u123"


def test_upload_files_calls_storage():
  payload = {"files": [{"name": "a.txt", "content_b64": "Zg=="}]}
  req, storage = make_request("urn:storage:files:upload_files:1", payload)
  resp = asyncio.run(storage_files_upload_files_v1(req))
  assert storage.upload_args[0] == "u123"
  assert [f.model_dump() for f in storage.upload_args[1]] == [{"name": "a.txt", "content_b64": "Zg==", "content_type": None}]
  assert storage.reindexed == "u123"
  assert resp.payload == {"files": [{"name": "a.txt", "content_b64": "Zg==", "content_type": None}]}


def test_delete_files_triggers_reindex():
  req, storage = make_request("urn:storage:files:delete_files:1", {"files": ["a.txt"]})
  _ = asyncio.run(storage_files_delete_files_v1(req))
  assert storage.deleted_files == ("u123", ["a.txt"])
  assert storage.reindexed == "u123"


def test_delete_folder_triggers_reindex():
  req, storage = make_request("urn:storage:files:delete_folder:1", {"path": "/docs"})
  _ = asyncio.run(storage_files_delete_folder_v1(req))
  assert storage.deleted == ("u123", "/docs")
  assert storage.reindexed == "u123"


def test_rename_file_calls_storage():
  req, storage = make_request(
    "urn:storage:files:rename_file:1",
    {"old_name": "a.txt", "new_name": "b.txt"},
  )
  _ = asyncio.run(storage_files_rename_file_v1(req))
  assert storage.renamed == ("u123", "a.txt", "b.txt")
  assert storage.reindexed == "u123"


def test_move_file_calls_storage():
  req, storage = make_request(
    "urn:storage:files:move_file:1",
    {"src": "a.txt", "dst": "docs/b.txt"},
  )
  _ = asyncio.run(storage_files_move_file_v1(req))
  assert storage.moved == ("u123", "a.txt", "docs/b.txt")
  assert storage.reindexed == "u123"


def test_get_metadata_returns_details():
  req, storage = make_request("urn:storage:files:get_metadata:1", {"name": "a.txt"})
  resp = asyncio.run(storage_files_get_metadata_v1(req))
  assert resp.payload == {
    "name": "a.txt",
    "size": 1,
    "content_type": "text/plain",
    "created_on": "now",
    "modified_on": "now",
  }
  assert storage.metadata_args == ("u123", "a.txt")
  assert storage.reindexed == "u123"


def test_get_usage_returns_summary():
  req, storage = make_request("urn:storage:files:get_usage:1", {})
  resp = asyncio.run(storage_files_get_usage_v1(req))
  assert resp.payload == {
    "total_size": 10,
    "by_type": [{"content_type": "text/plain", "size": 10}],
  }
  assert storage.usage_called == "u123"
  assert storage.reindexed == "u123"


def test_get_folder_files_returns_contents():
  req, storage = make_request("urn:storage:files:get_folder_files:1", {"path": "docs"})
  resp = asyncio.run(storage_files_get_folder_files_v1(req))
  assert resp.payload == {
    "path": "docs",
    "files": [
      {"path": "docs", "name": "a.txt", "url": "u/docs/a.txt", "content_type": "text/plain", "user_guid": None, "display_name": None, "gallery": False}
    ],
    "folders": [{"name": "sub", "empty": False}],
  }
  assert storage.list_folder_args == ("u123", "docs")
  assert storage.reindexed == "u123"


def test_set_gallery_updates_flag():
  req, storage = make_request(
    "urn:storage:files:set_gallery:1", {"name": "a.txt", "gallery": True}
  )
  resp = asyncio.run(storage_files_set_gallery_v1(req))
  assert resp.payload == {"name": "a.txt", "gallery": True}
  assert storage.gallery_args == ("u123", "a.txt", True)
  assert storage.reindexed == "u123"


def test_get_public_files_lists_files():
  req, storage = make_request("urn:storage:files:get_public_files:1", {})
  resp = asyncio.run(storage_files_get_public_files_v1(req))
  assert resp.payload == {
    "files": [
      {
        "path": "",
        "name": "a.txt",
        "url": "u/a.txt",
        "content_type": "text/plain",
        "user_guid": None,
        "display_name": None,
        "gallery": None,
      }
    ]
  }
  assert storage.list_public_called
  assert storage.reindexed is None


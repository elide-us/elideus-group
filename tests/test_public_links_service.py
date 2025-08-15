from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pathlib, sys, types

# Stub rpc package to avoid side effects from rpc.__init__
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Stub server modules to prevent importing full server app
server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
db_module_pkg = types.ModuleType('server.modules.db_module')
models_pkg = types.ModuleType('server.models')

class DbModule:  # minimal placeholder for import
  pass

db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
server_pkg.modules = modules_pkg
class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.db_module', db_module_pkg)
sys.modules.setdefault('server.models', models_pkg)

from rpc.public.links.services import public_links_get_home_links_v1, public_links_get_navbar_routes_v1


class DummyDb:
  async def run(self, op: str, args: dict):
    if op == "urn:public:links:get_home_links:1":
      assert args == {}
      return types.SimpleNamespace(rows=[{"title": "GitHub", "url": "https://github.com"}], rowcount=1)
    if op == "urn:public:links:get_navbar_routes:1":
      assert args == {"role_mask": 0}
      return types.SimpleNamespace(rows=[{"element_path": "/", "element_name": "Home", "element_icon": "home"}], rowcount=1)
    raise AssertionError("Unexpected op")


app = FastAPI()
app.state.db = DummyDb()


@app.post("/rpc_home")
async def rpc_home(request: Request):
  return await public_links_get_home_links_v1(request)


@app.post("/rpc_nav")
async def rpc_nav(request: Request):
  return await public_links_get_navbar_routes_v1(request)


client = TestClient(app)


def test_get_home_links_service():
  resp = client.post("/rpc_home", json={"op": "urn:public:links:get_home_links:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:links:get_home_links:1"
  assert data["payload"] == {
    "links": [{"title": "GitHub", "url": "https://github.com"}]
  }


def test_get_navbar_routes_service():
  resp = client.post("/rpc_nav", json={"op": "urn:public:links:get_navbar_routes:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:links:get_navbar_routes:1"
  assert data["payload"] == {
    "routes": [{"path": "/", "name": "Home", "icon": "home"}]
  }


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

class DbModule:  # minimal placeholder for import
  pass

db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
server_pkg.modules = modules_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.db_module', db_module_pkg)

from rpc.public.vars.services import public_vars_get_hostname_v1


class DummyDb:
  async def run(self, op: str, args: dict):
    assert op == "urn:public:vars:get_hostname:1"
    assert args == {}
    return types.SimpleNamespace(rows=[{"hostname": "example.com"}], rowcount=1)


app = FastAPI()
app.state.db = DummyDb()


@app.post("/rpc")
async def rpc_endpoint(request: Request):
  return await public_vars_get_hostname_v1(request)


client = TestClient(app)


def test_get_hostname_service():
  resp = client.post("/rpc", json={"op": "urn:public:vars:get_hostname:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_hostname:1"
  assert data["payload"] == {"hostname": "example.com"}


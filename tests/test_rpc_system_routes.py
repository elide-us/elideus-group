import asyncio
from fastapi import FastAPI, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest
from server.helpers import roles as role_helper

class DummyDB:
  def __init__(self):
    self.routes = {
      '/a': {
        'path': '/a',
        'name': 'A',
        'icon': 'home',
        'required_roles': 0,
        'sequence': 10,
      }
    }

  async def list_routes(self):
    return list(self.routes.values())

  async def list_roles(self):
    return []

  async def set_route(self, path, name, icon, required_roles, sequence):
    self.routes[path] = {
      'path': path,
      'name': name,
      'icon': icon,
      'required_roles': required_roles,
      'sequence': sequence,
    }

  async def delete_route(self, path):
    self.routes.pop(path, None)


class DummyMSSQL:
  def __init__(self):
    self.routes = {
      '/a': {
        'element_path': '/a',
        'element_name': 'A',
        'element_icon': 'home',
        'element_roles': 0,
        'element_sequence': 10,
      }
    }

  async def list_routes(self):
    return list(self.routes.values())

  async def list_roles(self):
    return []

  async def set_route(self, path, name, icon, required_roles, sequence):
    self.routes[path] = {
      'element_path': path,
      'element_name': name,
      'element_icon': icon,
      'element_roles': required_roles,
      'element_sequence': sequence,
    }

  async def delete_route(self, path):
    self.routes.pop(path, None)

async def make_app():
  app = FastAPI()
  app.state.database = DummyDB()
  app.state.auth = None
  app.state.permcap = None
  app.state.env = None
  await role_helper.load_roles(app.state.database)
  return app


async def make_app2():
  app = FastAPI()
  app.state.mssql = DummyMSSQL()
  app.state.auth = None
  app.state.permcap = None
  app.state.env = None
  await role_helper.load_roles(app.state.mssql)
  return app


def test_route_flow():
  app = asyncio.run(make_app())
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='urn:system:routes:list:1')
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert len(resp.payload.routes) == 1

  rpc = RPCRequest(op='urn:system:routes:set:1', payload={
    'path': '/b',
    'name': 'B',
    'icon': 'menu',
    'sequence': 20,
    'requiredRoles': []
  })
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert any(r.path == '/b' for r in resp.payload.routes)

  rpc = RPCRequest(op='urn:system:routes:delete:1', payload={'path': '/a'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert all(r.path != '/a' for r in resp.payload.routes)


def test_route_flow_v2():
  app = asyncio.run(make_app2())
  req = Request({'type': 'http', 'app': app, 'headers': []})

  rpc = RPCRequest(op='urn:system:routes:list:2')
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert len(resp.payload.routes) == 1

  rpc = RPCRequest(op='urn:system:routes:set:2', payload={
    'path': '/b',
    'name': 'B',
    'icon': 'menu',
    'sequence': 20,
    'requiredRoles': []
  })
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert any(r.path == '/b' for r in resp.payload.routes)

  rpc = RPCRequest(op='urn:system:routes:delete:2', payload={'path': '/a'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert all(r.path != '/a' for r in resp.payload.routes)

import asyncio
from fastapi import FastAPI, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest

class DummyDB:
  def __init__(self):
    self.data = {'A': '1'}

  async def list_config(self):
    return [{'key': k, 'value': v} for k, v in self.data.items()]

  async def set_config_value(self, key, value):
    self.data[key] = value

  async def delete_config_value(self, key):
    self.data.pop(key, None)

async def make_app():
  app = FastAPI()
  app.state.database = DummyDB()
  app.state.auth = None
  app.state.permcap = None
  app.state.env = None
  return app


def test_config_flow():
  app = asyncio.run(make_app())
  req = Request({'type': 'http', 'app': app, 'headers': []})

  rpc = RPCRequest(op='urn:admin:config:list:1')
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert len(resp.payload.items) == 1

  rpc = RPCRequest(op='urn:admin:config:set:1', payload={'key': 'B', 'value': '2'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert any(i.key == 'B' for i in resp.payload.items)

  rpc = RPCRequest(op='urn:admin:config:delete:1', payload={'key': 'A'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert all(i.key != 'A' for i in resp.payload.items)

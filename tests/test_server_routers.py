import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from rpc.models import RPCRequest, RPCResponse
from server.routers import rpc_router, web_router

async def _call_rpc():
  req = Request({'type': 'http', 'app': FastAPI()})
  return await rpc_router.post_root(RPCRequest(op='op'), req)


def test_rpc_router_delegates(monkeypatch):
  async def fake(req, request):
    return RPCResponse(op='x', payload=None)
  monkeypatch.setattr(rpc_router, 'handle_rpc_request', fake)
  resp = asyncio.run(_call_rpc())
  assert resp.op == 'x'


def test_web_router_serves_index():
  resp = asyncio.run(web_router.serve_react_app('foo'))
  assert isinstance(resp, FileResponse)
  assert resp.path.endswith('static/index.html')


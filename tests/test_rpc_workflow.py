import pytest
import asyncio
from fastapi import FastAPI, Request, HTTPException
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest, RPCResponse
import rpc.handler as rpc_handler
import rpc.frontend.handler as frontend_handler
import rpc.system.handler as admin_handler
import rpc.auth.handler as auth_handler
import rpc.auth.microsoft.handler as ms_handler

def test_rpc_dispatch_admin(monkeypatch):
  async def fake_admin(parts, rpc_request, request):
    return RPCResponse(op="admin", payload=None)
  monkeypatch.setattr(rpc_handler, "handle_system_request", fake_admin)
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  resp = asyncio.run(handle_rpc_request(RPCRequest(op="urn:system:test:1"), req))
  assert resp.op == "admin:view:default:1"

def test_rpc_unknown_domain():
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  with pytest.raises(HTTPException):
    asyncio.run(handle_rpc_request(RPCRequest(op="urn:bad:op:1"), req))

def test_frontend_handler_links(monkeypatch):
  async def fake_links(parts, req):
    return RPCResponse(op="links", payload=None)
  monkeypatch.setattr(frontend_handler, "handle_links_request", fake_links)
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  resp = asyncio.run(frontend_handler.handle_frontend_request(["links", "list"], RPCRequest(op='x'), req))
  assert resp.op == "links"

def test_admin_handler_unknown():
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  with pytest.raises(HTTPException):
    asyncio.run(admin_handler.handle_system_request(["nope"], RPCRequest(op='x'), req))

def test_auth_handler_ms(monkeypatch):
  async def fake_ms(rest, rpc_request, req):
    return RPCResponse(op="ms", payload=None)
  monkeypatch.setattr(auth_handler, "handle_ms_request", fake_ms)
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  rpc_req = RPCRequest(op="urn:auth:microsoft:login:1")
  resp = asyncio.run(auth_handler.handle_auth_request(["microsoft", "login"], rpc_req, req))
  assert resp.op == "ms"

def test_auth_handler_unknown():
  req = Request({"type": "http", "app": FastAPI(), 'headers': []})
  rpc_req = RPCRequest(op="urn:auth:other:1")
  with pytest.raises(HTTPException):
    asyncio.run(auth_handler.handle_auth_request(["other"], rpc_req, req))

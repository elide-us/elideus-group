import asyncio
from fastapi import FastAPI, Request

from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest

def test_get_version():
  app = FastAPI()
  app.state.version = "9.9.9"
  app.state.hostname = "unit-host"
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_version:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:version:1"
  assert response.payload.version == "9.9.9"

def test_get_hostname():
  app = FastAPI()
  app.state.version = "9.9.9"
  app.state.hostname = "unit-host"
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_hostname:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:hostname:1"
  assert response.payload.hostname == "unit-host"

def test_get_repo():
  app = FastAPI()
  app.state.version = "9.9.9"
  app.state.hostname = "unit-host"
  app.state.repo = "https://repo"
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_repo:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:repo:1"
  assert response.payload.repo == "https:///repo"
  assert response.payload.build == "https://repo/actions"


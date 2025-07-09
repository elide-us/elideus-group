import asyncio
from fastapi import FastAPI, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


def test_ms_user_login_stub():
  app = FastAPI()
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(
    op="urn:auth:microsoft:user_login:1",
    payload={"username": "tester", "email": "tester@example.com"}
  )
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:auth:microsoft:login_data:1"
  assert response.payload.username == "tester"
  assert response.payload.email == "tester@example.com"

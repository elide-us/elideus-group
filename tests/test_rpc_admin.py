import uuid
import asyncio
from fastapi import FastAPI, Request

from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest

def test_get_version():
    app = FastAPI()
    app.state.version = "1.0.0"
    app.state.hostname = "test-host"
    request = Request({"type": "http", "app": app})

    rpc_request = RPCRequest(op="urn:admin:vars:get_version:1", user_id=uuid.uuid4())
    response = asyncio.run(handle_rpc_request(rpc_request, request))

    assert response.op == "urn:admin:vars:version:1"
    assert response.payload.version == "1.0.0"

def test_get_hostname():
    app = FastAPI()
    app.state.version = "1.0.0"
    app.state.hostname = "test-host"
    request = Request({"type": "http", "app": app})

    rpc_request = RPCRequest(op="urn:admin:vars:get_hostname:1", user_id=uuid.uuid4())
    response = asyncio.run(handle_rpc_request(rpc_request, request))

    assert response.op == "urn:admin:vars:hostname:1"
    assert response.payload.hostname == "test-host"


import uuid
import asyncio
from importlib import reload

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

import server.config as config
from server import lifespan
from rpc.handler import handle_rpc_request
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.vars.services import get_version_v1, get_hostname_v1
from rpc.models import RPCRequest


def test_get_str_env_var_missing(monkeypatch):
    monkeypatch.delenv('MISSING_VAR', raising=False)
    with pytest.raises(RuntimeError):
        config._get_str_env_var('MISSING_VAR')


def test_lifespan_sets_state(monkeypatch):
    monkeypatch.setenv('VERSION', '1.2.3')
    monkeypatch.setenv('HOSTNAME', 'test-host')
    reload(config)
    reload(lifespan)
    app = FastAPI(lifespan=lifespan.lifespan)
    with TestClient(app) as client:
        assert client.app.state.version == '1.2.3'
        assert client.app.state.hostname == 'test-host'


def test_handle_rpc_request_invalid_prefix():
    app = FastAPI()
    request = Request({'type': 'http', 'app': app})
    rpc_request = RPCRequest(op='invalid')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(handle_rpc_request(rpc_request, request))
    assert exc.value.status_code == 400


def test_handle_rpc_request_unknown_domain():
    app = FastAPI()
    request = Request({'type': 'http', 'app': app})
    rpc_request = RPCRequest(op='urn:unknown:op:1')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(handle_rpc_request(rpc_request, request))
    assert exc.value.status_code == 404


def test_handle_vars_request_unknown_operation():
    app = FastAPI()
    request = Request({'type': 'http', 'app': app})
    with pytest.raises(HTTPException) as exc:
        asyncio.run(handle_vars_request(['unknown', '1'], request))
    assert exc.value.status_code == 404


def test_services_read_from_state():
    app = FastAPI()
    app.state.version = 'x.y.z'
    app.state.hostname = 'host'
    request = Request({'type': 'http', 'app': app})
    version_res = asyncio.run(get_version_v1(request))
    assert version_res.payload.version == 'x.y.z'
    host_res = asyncio.run(get_hostname_v1(request))
    assert host_res.payload.hostname == 'host'


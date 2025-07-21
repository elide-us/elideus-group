import asyncio
import pytest
from fastapi import FastAPI, Request

from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


class DummyDB:
    async def select_routes(self, role_mask=0):
        return [
            {
                "id": 1,
                "path": "/",
                "name": "Home",
                "icon": "home",
                "required_roles": 0,
                "sequence": 10,
            }
        ]
    async def select_links(self, role_mask=0):
        return [
            {
                "id": 1,
                "title": "Discord",
                "url": "https://link",
                "required_roles": 0,
            }
        ]

    async def get_config_value(self, key):
        return {
            "Version": "v1.2.3",
            "Hostname": "unit-host",
            "Repo": "https://repo",
        }.get(key)

    async def select_users(self):
        return [{"guid": "uid", "display_name": "User"}]

    async def get_user_profile(self, guid):
        return {
            "guid": guid,
            "display_name": "User",
            "email": "u@example.com",
            "profile_image": "img",
            "display_email": False,
            "credits": getattr(self, "credits", 0),
            "provider_name": "microsoft",
            "rotation_token": None,
            "rotation_expires": None,
        }

    async def set_user_credits(self, guid, credits):
        self.credits = credits

class DummyPermCap:
    def filter_routes(self, data, role_mask):
        return data

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("VERSION", "v1.2.3")
    monkeypatch.setenv("HOSTNAME", "unit-host")
    monkeypatch.setenv("REPO", "https://repo")
    monkeypatch.setenv("DISCORD_SECRET", "token")

@pytest.fixture
def app():
    app = FastAPI()
    # initialize the env module *after* the os.environ values are patched
    env_module = EnvironmentModule(app)
    # services do `request.app.state.env`, so set it here
    app.state.env = env_module
    app.state.database = DummyDB()
    app.state.permcap = DummyPermCap()
    return app

def test_get_version(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:vars:get_version:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:vars:version:1:view:default:1"
    assert resp.payload.version == "v1.2.3"

def test_get_hostname(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:vars:get_hostname:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:vars:hostname:1:view:default:1"
    assert resp.payload.hostname == "unit-host"

def test_get_repo(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:vars:get_repo:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:vars:repo:1:view:default:1"
    assert resp.payload.repo == "https://repo"

def test_get_ffmpeg_version(app, monkeypatch):
    async def fake_exec(*args, **kwargs):
        class Proc:
            async def communicate(self):
                return (b"ffmpeg version 6.0", b"")
        return Proc()

    import rpc.admin.vars.services as services
    monkeypatch.setattr(services.asyncio, "create_subprocess_exec", fake_exec)

    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:vars:get_ffmpeg_version:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:vars:ffmpeg_version:1:view:default:1"
    assert resp.payload.ffmpeg_version == "ffmpeg version 6.0"

def test_get_links(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:links:get_home:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:links:home:1:view:default:1"
    assert len(resp.payload.links) == 1
    assert resp.payload.links[0].title == "Discord"

def test_get_routes(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:links:get_routes:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:links:routes:1:view:default:1"
    assert len(resp.payload.routes) == 1
    assert resp.payload.routes[0].path == "/"

def test_get_users(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:users:list:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:users:list:1:view:default:1"
    assert len(resp.payload.users) == 1
    assert resp.payload.users[0].displayName == "User"

def test_get_user_profile(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:users:get_profile:1", payload={"userGuid": "uid"})
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:users:get_profile:1:view:default:1"
    assert resp.payload.email == "u@example.com"

def test_set_user_credits(app):
    request = Request({"type": "http", "app": app})
    rpc_request = RPCRequest(op="urn:admin:users:set_credits:1", payload={"userGuid": "uid", "credits": 100})
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:admin:users:set_credits:1:view:default:1"
    assert resp.payload.credits == 100


import asyncio
import pytest
from fastapi import FastAPI, Request

from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


from server.helpers import roles as role_helper


class DummyDB:
    def __init__(self):
        self.role_map = {}
        self.roles = {"ROLE_REGISTERED": 1, "ROLE_SYSTEM_ADMIN": 2}

    async def list_roles(self):
        return [{"name": n, "display": n, "mask": m} for n, m in self.roles.items()]

    async def select_routes(self, role_mask=0):
        routes = [
            {
                "id": 1,
                "recid": 1,
                "path": "/",
                "element_path": "/",
                "name": "Home",
                "element_name": "Home",
                "icon": "home",
                "element_icon": "home",
                "required_roles": 0,
                "element_roles": 0,
                "sequence": 10,
                "element_sequence": 10,
            },
            {
                "id": 2,
                "recid": 2,
                "path": "/gallery",
                "element_path": "/gallery",
                "name": "Gallery",
                "element_name": "Gallery",
                "icon": "gallery",
                "element_icon": "gallery",
                "required_roles": 0,
                "element_roles": 0,
                "sequence": 20,
                "element_sequence": 20,
            },
            {
                "id": 3,
                "recid": 3,
                "path": "/file-manager",
                "element_path": "/file-manager",
                "name": "File Manager",
                "element_name": "File Manager",
                "icon": "files",
                "element_icon": "files",
                "required_roles": self.roles["ROLE_REGISTERED"],
                "element_roles": self.roles["ROLE_REGISTERED"],
                "sequence": 30,
                "element_sequence": 30,
            },
            {
                "id": 4,
                "recid": 4,
                "path": "/user-admin",
                "element_path": "/user-admin",
                "name": "User Admin",
                "element_name": "User Admin",
                "icon": "admin",
                "element_icon": "admin",
                "required_roles": self.roles["ROLE_SYSTEM_ADMIN"] | self.roles["ROLE_REGISTERED"],
                "element_roles": self.roles["ROLE_SYSTEM_ADMIN"] | self.roles["ROLE_REGISTERED"],
                "sequence": 40,
                "element_sequence": 40,
            },
        ]
        return [
            r
            for r in routes
            if r["required_roles"] == 0
            or (r["required_roles"] & role_mask) == r["required_roles"]
        ]

    async def get_user_roles(self, guid):
        return self.role_map.get(guid, 0)
    async def select_links(self, role_mask=0):
        return [
            {
                "id": 1,
                "recid": 1,
                "title": "Discord",
                "element_title": "Discord",
                "url": "https://link",
                "element_url": "https://link",
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


class DummyAuth:
    async def decode_bearer_token(self, token):
        return {"guid": token}

class DummyStorage:
    async def get_user_folder_size(self, guid):
        return 0
    async def user_folder_exists(self, guid):
        return False
    async def ensure_user_folder(self, guid):
        return None

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("VERSION", "v1.2.3")
    monkeypatch.setenv("HOSTNAME", "unit-host")
    monkeypatch.setenv("REPO", "https://repo")
    monkeypatch.setenv("DISCORD_SECRET", "token")
    monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")

@pytest.fixture
def app():
    app = FastAPI()
    # initialize the env module *after* the os.environ values are patched
    env_module = EnvironmentModule(app)
    # services do `request.app.state.env`, so set it here
    app.state.env = env_module
    db = DummyDB()
    asyncio.run(role_helper.load_roles(db))
    db.role_map = {"admin": role_helper.ROLES["ROLE_SYSTEM_ADMIN"], "uid": 0}
    app.state.database = db
    app.state.mssql = db
    app.state.permcap = DummyPermCap()
    app.state.auth = DummyAuth()
    app.state.storage = DummyStorage()
    return app

def test_get_version(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_version:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:version:1:view:default:1"
    assert resp.payload.version == "v1.2.3"

def test_get_version_v2(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_version:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:version:2:view:default:1"
    assert resp.payload.version == "v1.2.3"

def test_get_hostname(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_hostname:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:hostname:1:view:default:1"
    assert resp.payload.hostname == "unit-host"

def test_get_hostname_v2(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_hostname:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:hostname:2:view:default:1"
    assert resp.payload.hostname == "unit-host"

def test_get_repo(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_repo:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:repo:1:view:default:1"
    assert resp.payload.repo == "https://repo"

def test_get_repo_v2(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_repo:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:repo:2:view:default:1"
    assert resp.payload.repo == "https://repo"

def test_get_ffmpeg_version(app, monkeypatch):
    async def fake_exec(*args, **kwargs):
        class Proc:
            async def communicate(self):
                return (b"ffmpeg version 6.0", b"")
        return Proc()

    import rpc.frontend.vars.services as services
    monkeypatch.setattr(services.asyncio, "create_subprocess_exec", fake_exec)

    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:vars:get_ffmpeg_version:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:vars:ffmpeg_version:1:view:default:1"
    assert resp.payload.ffmpeg_version == "ffmpeg version 6.0"

def test_get_links(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:links:get_home:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:home:1:view:default:1"
    assert len(resp.payload.links) == 1
    assert resp.payload.links[0].title == "Discord"

def test_get_links_v2(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:links:get_home:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:home:2:view:default:1"
    assert len(resp.payload.links) == 1
    assert resp.payload.links[0].title == "Discord"

def test_get_routes_not_logged_in(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:1:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery"]

def test_get_routes_not_logged_in_v2(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:2:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery"]


def test_get_routes_logged_in(app):
    scope = {"type": "http", "app": app, "headers": [(b"authorization", b"Bearer uid")]} 
    request = Request(scope)
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:1:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery", "/file-manager"]

def test_get_routes_logged_in_v2(app):
    scope = {"type": "http", "app": app, "headers": [(b"authorization", b"Bearer uid")]} 
    request = Request(scope)
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:2:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery", "/file-manager"]


def test_get_routes_admin(app):
    scope = {"type": "http", "app": app, "headers": [(b"authorization", b"Bearer admin")]} 
    request = Request(scope)
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:1:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery", "/file-manager", "/user-admin"]

def test_get_routes_admin_v2(app):
    scope = {"type": "http", "app": app, "headers": [(b"authorization", b"Bearer admin")]} 
    request = Request(scope)
    rpc_request = RPCRequest(op="urn:frontend:links:get_routes:2")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:frontend:links:routes:2:view:default:1"
    assert [r.path for r in resp.payload.routes] == ["/", "/gallery", "/file-manager", "/user-admin"]

def test_get_users(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:system:users:list:1")
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:system:users:list:1:view:default:1"
    assert len(resp.payload.users) == 1
    assert resp.payload.users[0].displayName == "User"

def test_get_user_profile(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:account:users:get_profile:1", payload={"userGuid": "uid"})
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:account:users:get_profile:1:view:default:1"
    assert resp.payload.email == "u@example.com"

def test_set_user_credits(app):
    request = Request({"type": "http", "app": app, 'headers': []})
    rpc_request = RPCRequest(op="urn:account:users:set_credits:1", payload={"userGuid": "uid", "credits": 100})
    resp = asyncio.run(handle_rpc_request(rpc_request, request))

    assert resp.op == "urn:account:users:set_credits:1:view:default:1"
    assert resp.payload.credits == 100


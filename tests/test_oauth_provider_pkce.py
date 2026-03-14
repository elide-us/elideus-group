import asyncio
import pathlib
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from jose import jwt

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from server.routers import oauth_router
from server.modules import oauth_module as oauth_module_mod
from server.modules.oauth_module import OauthModule


def _request_with_gateway(gateway):
  return SimpleNamespace(
    app=SimpleNamespace(
      state=SimpleNamespace(
        mcp_gateway=gateway,
        auth=SimpleNamespace(jwt_secret="test-secret"),
      )
    ),
    client=None,
    headers={},
  )


def test_provider_login_includes_pkce_and_state_verifier():
  gateway = SimpleNamespace(
    hostname="example.test",
    oauth=SimpleNamespace(auth=SimpleNamespace(providers={"microsoft": SimpleNamespace(audience="client-id")})),
  )
  request = _request_with_gateway(gateway)
  flow = oauth_router._sign_flow_state(request, {"client_id": "mcp-client"})

  response = asyncio.run(oauth_router.get_oauth_provider_login(request, "microsoft", flow))

  parsed = urlparse(response.headers["location"])
  params = parse_qs(parsed.query)
  assert params["code_challenge_method"] == ["S256"]
  assert params["code_challenge"] and params["code_challenge"][0]

  state_payload = jwt.decode(params["state"][0], "test-secret", algorithms=["HS256"])
  assert state_payload["provider"] == "microsoft"
  assert state_payload.get("provider_code_verifier")


def test_provider_callback_uses_verifier_and_handles_provider_error():
  captured = {}

  class FakeOauth:
    auth = SimpleNamespace(providers={"microsoft": SimpleNamespace(audience="provider-client-id")})
    env = SimpleNamespace(get=lambda _key: "provider-secret")

    async def exchange_code_for_tokens(self, **kwargs):
      captured.update(kwargs)
      return "id-token", "access-token"

    def normalize_provider_identifier(self, uid):
      return uid

    async def resolve_user(self, provider, provider_uid, profile, payload):
      return {"guid": "user-guid", "recid": 7}

  class FakeAuth:
    async def handle_auth_login(self, provider, id_token, access_token):
      return "provider-uid", {"email": "user@example.com"}, {}

  class FakeGateway:
    hostname = "example.test"
    oauth = FakeOauth()
    auth = FakeAuth()

    async def check_user_mcp_role(self, _user_guid):
      return True

    async def get_client(self, _client_id):
      return {"recid": 3}

    async def link_client_to_user(self, _client_id, _users_recid):
      return None

    async def create_authorization_code(self, **_kwargs):
      return "auth-code"

  request = _request_with_gateway(FakeGateway())
  state = oauth_router._sign_flow_state(
    request,
    {
      "provider": "microsoft",
      "provider_code_verifier": "verifier-abc",
      "flow": {
        "client_id": "client-1",
        "code_challenge": "challenge",
        "code_challenge_method": "S256",
        "redirect_uri": "https://client/callback",
        "scope": "mcp:data:read",
        "state": "xyz",
      },
    },
  )

  response = asyncio.run(
    oauth_router.get_oauth_provider_callback(
      request,
      "microsoft",
      code="provider-code",
      state=state,
    )
  )
  assert response.headers["location"].startswith("https://client/callback?")
  assert captured["code_verifier"] == "verifier-abc"

  with pytest.raises(HTTPException) as exc_info:
    asyncio.run(
      oauth_router.get_oauth_provider_callback(
        request,
        "microsoft",
        error="invalid_request",
        error_description="PKCE is required",
      )
    )
  assert exc_info.value.status_code == 400
  assert "Provider authentication failed: PKCE is required" == exc_info.value.detail


def test_exchange_code_for_tokens_includes_code_verifier(monkeypatch):
  captured = {}

  class FakeResponse:
    status = 200

    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      return False

    async def json(self):
      return {"id_token": "id", "access_token": "access"}

  class FakeSession:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      return False

    def post(self, _url, data):
      captured.update(data)
      return FakeResponse()

  monkeypatch.setattr(oauth_module_mod.aiohttp, "ClientSession", lambda: FakeSession())

  module = OauthModule.__new__(OauthModule)
  tokens = asyncio.run(
    OauthModule.exchange_code_for_tokens(
      module,
      code="auth-code",
      client_id="client-id",
      client_secret="secret",
      redirect_uri="https://example.test/oauth/callback/microsoft",
      provider="microsoft",
      code_verifier="pkce-verifier",
    )
  )

  assert tokens == ("id", "access")
  assert captured["code_verifier"] == "pkce-verifier"

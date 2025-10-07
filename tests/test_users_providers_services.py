import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from server.models import RPCRequest, RPCResponse

from rpc.users.providers import services as user_services
from rpc.auth.providers import services as auth_services


class DummyModule:
  def __init__(self):
    self.calls = []
    self.get_result = None
    self.create_result = None

  async def set_provider(self, guid, provider, *, code=None, id_token=None, access_token=None):
    self.calls.append(("set", {
      "guid": guid,
      "provider": provider,
      "code": code,
      "id_token": id_token,
      "access_token": access_token,
    }))

  async def link_provider(self, guid, provider, *, code=None, id_token=None, access_token=None):
    self.calls.append(("link", {
      "guid": guid,
      "provider": provider,
      "code": code,
      "id_token": id_token,
      "access_token": access_token,
    }))

  async def unlink_provider(self, guid, provider, *, new_default=None):
    self.calls.append(("unlink", {
      "guid": guid,
      "provider": provider,
      "new_default": new_default,
    }))

  async def get_by_provider_identifier(self, provider, provider_identifier):
    self.calls.append(("get", {
      "provider": provider,
      "provider_identifier": provider_identifier,
    }))
    return self.get_result

  async def create_from_provider(
    self,
    provider,
    provider_identifier,
    provider_email,
    provider_displayname,
    provider_profile_image,
  ):
    self.calls.append(("create", {
      "provider": provider,
      "provider_identifier": provider_identifier,
      "provider_email": provider_email,
      "provider_displayname": provider_displayname,
      "provider_profile_image": provider_profile_image,
    }))
    return self.create_result

  async def unlink_last_provider(self, guid, provider):
    self.calls.append(("unlink_last", {
      "guid": guid,
      "provider": provider,
    }))


class DummyRequest:
  def __init__(self, module):
    self.app = SimpleNamespace(state=SimpleNamespace(user_providers=module))
    self.headers = {}


def make_rpc_request(op, payload=None, version=1):
  return RPCRequest(op=op, payload=payload or {}, version=version)


def stub_unbox(module, rpc_request, auth_ctx=None):
  async def fake_unbox(request):
    return rpc_request, auth_ctx or SimpleNamespace(user_guid="user-1"), None
  return fake_unbox


def restore(module, attr, value):
  setattr(module, attr, value)


def test_set_provider_delegates_to_module():
  module = DummyModule()
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:set_provider:1",
    {"provider": "microsoft", "id_token": "id", "access_token": "acc"},
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request)
  try:
    resp = asyncio.run(user_services.users_providers_set_provider_v1(req))
  finally:
    restore(user_services, "unbox_request", original)
  assert isinstance(resp, RPCResponse)
  assert resp.op == rpc_request.op
  assert resp.version == 1
  assert resp.payload["provider"] == "microsoft"
  assert module.calls[0][0] == "set"
  assert module.calls[0][1]["guid"] == "user-1"


def test_link_provider_requires_code_for_google():
  module = DummyModule()
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:link_provider:1",
    {"provider": "google"},
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request)
  with pytest.raises(HTTPException):
    asyncio.run(user_services.users_providers_link_provider_v1(req))
  restore(user_services, "unbox_request", original)
  assert not module.calls


def test_link_provider_delegates_to_module():
  module = DummyModule()
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:link_provider:1",
    {"provider": "discord", "code": "auth"},
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request)
  try:
    resp = asyncio.run(user_services.users_providers_link_provider_v1(req))
  finally:
    restore(user_services, "unbox_request", original)
  assert resp.payload == {"provider": "discord"}
  assert module.calls[0][0] == "link"
  assert module.calls[0][1]["guid"] == "user-1"


def test_unlink_provider_delegates_to_module():
  module = DummyModule()
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:unlink_provider:1",
    {"provider": "google", "new_default": "microsoft"},
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request)
  try:
    resp = asyncio.run(user_services.users_providers_unlink_provider_v1(req))
  finally:
    restore(user_services, "unbox_request", original)
  assert resp.payload == {"provider": "google"}
  assert module.calls[0] == ("unlink", {"guid": "user-1", "provider": "google", "new_default": "microsoft"})


def test_get_by_provider_identifier_returns_module_value():
  module = DummyModule()
  module.get_result = {"guid": "user-1"}
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:get_by_provider_identifier:1",
    {"provider": "google", "provider_identifier": "pid"},
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request, auth_ctx=None)
  try:
    resp = asyncio.run(user_services.users_providers_get_by_provider_identifier_v1(req))
  finally:
    restore(user_services, "unbox_request", original)
  assert resp.payload == {"guid": "user-1"}
  assert module.calls[0][0] == "get"


def test_create_from_provider_returns_module_value():
  module = DummyModule()
  module.create_result = {"guid": "user-1"}
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:users:providers:create_from_provider:1",
    {
      "provider": "google",
      "provider_identifier": "pid",
      "provider_email": "user@example.com",
      "provider_displayname": "User",
      "provider_profile_image": None,
    },
  )
  original = user_services.unbox_request
  user_services.unbox_request = stub_unbox(user_services, rpc_request, auth_ctx=None)
  try:
    resp = asyncio.run(user_services.users_providers_create_from_provider_v1(req))
  finally:
    restore(user_services, "unbox_request", original)
  assert resp.payload == {"guid": "user-1"}
  assert module.calls[0][0] == "create"


def test_auth_unlink_last_provider_delegates_to_module():
  module = DummyModule()
  req = DummyRequest(module)
  rpc_request = make_rpc_request(
    "urn:auth:providers:unlink_last_provider:1",
    {"guid": "u1", "provider": "google"},
  )
  original = auth_services.unbox_request
  auth_services.unbox_request = stub_unbox(auth_services, rpc_request, auth_ctx=None)
  try:
    resp = asyncio.run(auth_services.auth_providers_unlink_last_provider_v1(req))
  finally:
    restore(auth_services, "unbox_request", original)
  assert resp.payload == {"ok": True}
  assert module.calls[0] == ("unlink_last", {"guid": "u1", "provider": "google"})


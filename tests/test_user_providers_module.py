import asyncio
from types import SimpleNamespace
import uuid

import pytest
from fastapi import FastAPI, HTTPException

from server.modules.user_providers_module import UserProvidersModule
from server.registry.types import DBRequest
from server.registry.system.config import get_config_request
from server.registry.users.content.profile import (
  get_profile_request,
  update_if_unedited_request,
)
from server.registry.users.security.identities import (
  create_from_provider_request,
  get_by_provider_identifier_request,
  get_user_by_email_request,
  link_provider_request,
  set_provider_request,
  unlink_last_provider_request,
  unlink_provider_request,
)
from server.registry.users.security.sessions import revoke_provider_tokens_request


class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount


def _normalize_db_call(op, args=None):
  if isinstance(op, DBRequest):
    args = op.params
    op = op.op
  return op, args or {}


class ReadyStub:
  async def on_ready(self):
    return None


class DummyDb(ReadyStub):
  def __init__(self):
    self.calls = []
    self._handlers = {}

  def respond(self, op: str, handler):
    self._handlers[op] = handler

  async def run(self, op, args=None):
    key, params = _normalize_db_call(op, args)
    self.calls.append((key, params))
    handler = self._handlers.get(key)
    if handler:
      return handler(params)
    return DBRes()


class DummyAuth(ReadyStub):
  def __init__(self, providers=None, login_result=None):
    self.providers = providers or {}
    self.login_result = login_result or ("pid", {"email": "", "username": ""}, {})
    self.logins = []

  async def handle_auth_login(self, provider, id_token, access_token):
    self.logins.append((provider, id_token, access_token))
    return self.login_result


class DummyOauth(ReadyStub):
  def __init__(self, result=("id", "access")):
    self.result = result
    self.calls = []

  async def exchange_code_for_tokens(self, code, client_id, client_secret, redirect_uri, provider):
    self.calls.append((code, client_id, client_secret, redirect_uri, provider))
    return self.result


class DummyEnv(ReadyStub):
  def __init__(self, values=None):
    self.values = values or {}

  def get(self, key):
    if key not in self.values:
      raise RuntimeError(f"missing env {key}")
    return self.values[key]


def build_module(db=None, auth=None, oauth=None, env=None):
  app = FastAPI()
  db = db or DummyDb()
  auth = auth or DummyAuth()
  oauth = oauth or DummyOauth()
  env = env or DummyEnv()
  app.state.db = db
  app.state.auth = auth
  app.state.oauth = oauth
  app.state.env = env
  module = UserProvidersModule(app)
  asyncio.run(module.startup())
  return module, db, auth, oauth, env


def test_set_provider_calls_db_updates_profile():
  auth = DummyAuth(
    providers={"microsoft": SimpleNamespace(audience="client")},
    login_result=("pid", {"email": "e", "username": "n"}, {}),
  )
  module, db, *_ = build_module(auth=auth)
  asyncio.run(
    module.set_provider(
      guid="u1",
      provider="microsoft",
      id_token="id",
      access_token="acc",
    )
  )
  set_req = set_provider_request(guid="u1", provider="microsoft")
  update_req = update_if_unedited_request(guid="u1", email="e", display_name="n")
  assert (set_req.op, set_req.params) in db.calls
  assert (update_req.op, update_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_set_provider_defaults_blank_profile():
  auth = DummyAuth(
    providers={"microsoft": SimpleNamespace(audience="client")},
    login_result=("pid", {"email": "", "username": ""}, {}),
  )
  module, db, *_ = build_module(auth=auth)
  asyncio.run(
    module.set_provider(
      guid="u1",
      provider="microsoft",
      id_token="id",
      access_token="acc",
    )
  )
  update_req = update_if_unedited_request(guid="u1", email="", display_name="User")
  assert (update_req.op, update_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_link_provider_google_normalizes_identifier():
  auth = DummyAuth(
    providers={"google": SimpleNamespace(audience="client-id")},
    login_result=("google-id", {}, {}),
  )
  oauth = DummyOauth(result=("id", "acc"))
  env = DummyEnv({"GOOGLE_AUTH_SECRET": "secret"})
  db = DummyDb()
  config_req = get_config_request("Hostname")
  db.respond(config_req.op, lambda _: DBRes(rows=[{"value": "redirect"}]))
  module, db, *_ = build_module(db=db, auth=auth, oauth=oauth, env=env)
  asyncio.run(
    module.link_provider(
      guid="u1",
      provider="google",
      code="authcode",
    )
  )
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "google-id"))
  link_req = link_provider_request(
    guid="u1",
    provider="google",
    provider_identifier=expected,
  )
  assert (link_req.op, link_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_link_provider_discord_normalizes_identifier():
  auth = DummyAuth(
    providers={"discord": SimpleNamespace(audience="client-id")},
    login_result=("discord-id", {}, {}),
  )
  oauth = DummyOauth(result=(None, "acc"))
  env = DummyEnv({"DISCORD_AUTH_SECRET": "secret"})
  db = DummyDb()
  config_req = get_config_request("Hostname")
  db.respond(config_req.op, lambda _: DBRes(rows=[{"value": "redirect"}]))
  module, db, *_ = build_module(db=db, auth=auth, oauth=oauth, env=env)
  asyncio.run(
    module.link_provider(
      guid="u1",
      provider="discord",
      code="authcode",
    )
  )
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "discord-id"))
  link_req = link_provider_request(
    guid="u1",
    provider="discord",
    provider_identifier=expected,
  )
  assert (link_req.op, link_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_link_provider_microsoft_normalizes_identifier():
  auth = DummyAuth(
    providers={"microsoft": SimpleNamespace(audience="client-id")},
    login_result=("ms-id", {}, {}),
  )
  module, db, *_ = build_module(auth=auth)
  asyncio.run(
    module.link_provider(
      guid="u1",
      provider="microsoft",
      id_token="id",
      access_token="acc",
    )
  )
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "ms-id"))
  link_req = link_provider_request(
    guid="u1",
    provider="microsoft",
    provider_identifier=expected,
  )
  assert (link_req.op, link_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_unlink_non_default_provider_retains_tokens():
  db = DummyDb()
  profile_req = get_profile_request(guid="u1")
  db.respond(profile_req.op, lambda _: DBRes(rows=[{"default_provider": "microsoft"}]))
  unlink_req = unlink_provider_request(guid="u1", provider="google")
  db.respond(unlink_req.op, lambda _: DBRes(rows=[{"providers_remaining": 1}], rowcount=1))
  module, db, *_ = build_module(db=db)
  asyncio.run(
    module.unlink_provider(
      guid="u1",
      provider="google",
    )
  )
  revoke_req = revoke_provider_tokens_request(guid="u1", provider="google")
  assert revoke_req.op not in [op for op, _ in db.calls]
  asyncio.run(module.shutdown())


def test_unlink_default_provider_without_new_default_raises():
  db = DummyDb()
  profile_req = get_profile_request(guid="u1")
  db.respond(profile_req.op, lambda _: DBRes(rows=[{"default_provider": "google"}]))
  unlink_req = unlink_provider_request(guid="u1", provider="google")
  db.respond(unlink_req.op, lambda _: DBRes(rows=[{"providers_remaining": 1}], rowcount=1))
  module, *_ = build_module(db=db)
  with pytest.raises(HTTPException) as exc:
    asyncio.run(
      module.unlink_provider(
        guid="u1",
        provider="google",
      )
    )
  assert exc.value.status_code == 400
  asyncio.run(module.shutdown())


def test_unlink_default_provider_sets_new_default_and_revokes_tokens():
  db = DummyDb()
  profile_req = get_profile_request(guid="u1")
  db.respond(profile_req.op, lambda _: DBRes(rows=[{"default_provider": "google"}]))
  unlink_req = unlink_provider_request(guid="u1", provider="google")
  db.respond(unlink_req.op, lambda _: DBRes(rows=[{"providers_remaining": 1}], rowcount=1))
  module, db, *_ = build_module(db=db)
  asyncio.run(
    module.unlink_provider(
      guid="u1",
      provider="google",
      new_default="microsoft",
    )
  )
  set_req = set_provider_request(guid="u1", provider="microsoft")
  revoke_req = revoke_provider_tokens_request(guid="u1", provider="google")
  assert (set_req.op, set_req.params) in db.calls
  assert (revoke_req.op, revoke_req.params) in db.calls
  asyncio.run(module.shutdown())


def test_unlink_last_provider_soft_deletes_and_revokes():
  db = DummyDb()
  profile_req = get_profile_request(guid="u1")
  db.respond(profile_req.op, lambda _: DBRes(rows=[{"default_provider": "google"}]))
  unlink_req = unlink_provider_request(guid="u1", provider="google")
  db.respond(unlink_req.op, lambda _: DBRes(rows=[{"providers_remaining": 0}], rowcount=1))
  last_req = unlink_last_provider_request(guid="u1", provider="google")
  db.respond(last_req.op, lambda _: DBRes([], 1))
  module, db, *_ = build_module(db=db)
  asyncio.run(
    module.unlink_provider(
      guid="u1",
      provider="google",
    )
  )
  assert (last_req.op, last_req.params) in db.calls
  revoke_req = revoke_provider_tokens_request(guid="u1", provider="google")
  assert revoke_req.op not in [op for op, _ in db.calls]
  asyncio.run(module.shutdown())


def test_create_from_provider_checks_email_conflict():
  db = DummyDb()
  email_req = get_user_by_email_request(email="exists@example.com")
  db.respond(email_req.op, lambda _: DBRes(rows=[{"guid": "u1"}]))
  module, *_ = build_module(db=db)
  with pytest.raises(HTTPException) as exc:
    asyncio.run(
      module.create_from_provider(
        provider="google",
        provider_identifier="pid",
        provider_email="exists@example.com",
        provider_displayname="Name",
        provider_profile_image=None,
      )
    )
  assert exc.value.status_code == 409
  asyncio.run(module.shutdown())


def test_create_from_provider_returns_row():
  db = DummyDb()
  email_req = get_user_by_email_request(email="new@example.com")
  db.respond(email_req.op, lambda _: DBRes(rows=[]))
  create_req = create_from_provider_request(
    provider="google",
    provider_identifier="pid",
    provider_email="new@example.com",
    provider_displayname="Name",
    provider_profile_image=None,
  )
  db.respond(create_req.op, lambda params: DBRes(rows=[{"guid": "u1"}]))
  module, db, *_ = build_module(db=db)
  row = asyncio.run(
    module.create_from_provider(
      provider="google",
      provider_identifier="pid",
      provider_email="new@example.com",
      provider_displayname="Name",
      provider_profile_image=None,
    )
  )
  assert row == {"guid": "u1"}
  asyncio.run(module.shutdown())


def test_get_by_provider_identifier_returns_row():
  db = DummyDb()
  lookup_req = get_by_provider_identifier_request(provider="google", provider_identifier="pid")
  db.respond(lookup_req.op, lambda params: DBRes(rows=[{"guid": "u1"}]))
  module, db, *_ = build_module(db=db)
  row = asyncio.run(
    module.get_by_provider_identifier(
      provider="google",
      provider_identifier="pid",
    )
  )
  assert row == {"guid": "u1"}
  asyncio.run(module.shutdown())


def test_set_provider_missing_provider_config_raises():
  auth = DummyAuth(providers={})
  module, *_ = build_module(auth=auth)
  with pytest.raises(HTTPException) as exc:
    asyncio.run(
      module.set_provider(
        guid="u1",
        provider="google",
        code="code",
      )
    )
  assert exc.value.status_code == 500
  asyncio.run(module.shutdown())


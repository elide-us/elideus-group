import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from server.registry.users.security.identities import mssql as identities_registry
from server.registry.types import DBResponse


def test_create_from_provider_inserts_profile_image(monkeypatch):
  executed = []
  args = {
    "provider": "microsoft",
    "provider_identifier": str(uuid4()),
    "provider_email": "user@example.com",
    "provider_displayname": "User",
    "provider_profile_image": "img",
  }

  class DummyCursor:
    async def execute(self, sql, params):
      executed.append(sql.lower())

  @asynccontextmanager
  async def dummy_transaction():
    yield DummyCursor()

  lookups = []

  async def fake_get_provider(provider, cursor=None):
    lookups.append((provider, cursor is not None))
    return 1

  async def fake_run_json_one(sql, params=(), *, meta=None):
    q = sql.strip().lower()
    if q.startswith("select recid from auth_providers"):
      return DBResponse(rows=[{"recid": 1}], rowcount=1)
    if q.startswith("select users_guid from users_auth"):
      return DBResponse(rows=[], rowcount=0)
    return DBResponse(rows=[{"guid": "gid", "profile_image": args["provider_profile_image"]}], rowcount=1)

  async def fake_run_exec(sql, params=(), *, meta=None):
    executed.append(sql.lower())
    return DBResponse(rows=[], rowcount=1)

  monkeypatch.setattr(identities_registry, "transaction", dummy_transaction)
  monkeypatch.setattr(identities_registry, "get_auth_provider_recid", fake_get_provider)
  monkeypatch.setattr(identities_registry, "run_json_one", fake_run_json_one)
  monkeypatch.setattr(identities_registry, "run_exec", fake_run_exec)
  res = asyncio.run(identities_registry.create_from_provider_v1(args))

  assert any("insert into users_profileimg" in sql for sql in executed)
  assert any("insert into users_roles" in sql for sql in executed)
  assert res.rows
  assert res.rows[0]["profile_image"] == "img"
  assert lookups == [("microsoft", False)]


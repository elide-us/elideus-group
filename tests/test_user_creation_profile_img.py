import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from server.registry.types import DBResponse
from server.registry.account.providers import mssql as users_providers_mssql


def test_create_from_provider_inserts_profile_image(monkeypatch):
  executed: list[str] = []
  fetch_iter = iter([(None,)])

  class DummyCursor:
    async def execute(self, sql, params):
      executed.append(sql.lower())

    async def fetchone(self):
      return next(fetch_iter, None)

  @asynccontextmanager
  async def dummy_transaction():
    yield DummyCursor()

  async def fake_run_exec(sql, params):
    executed.append(sql.lower())
    return DBResponse(rowcount=1)

  async def fake_run_json_one(sql, params):
    query = sql.strip().lower()
    if "select users_guid from users_auth" in query:
      return DBResponse()
    if "from vw_account_user_profile" in query:
      return DBResponse(rows=[{"guid": "gid", "profile_image": args["provider_profile_image"]}], rowcount=1)
    raise AssertionError(f"Unexpected query: {sql}")

  async def fake_get_auth_provider_recid(provider, *, cursor=None):
    return 1

  monkeypatch.setattr(users_providers_mssql, "transaction", dummy_transaction)
  monkeypatch.setattr(users_providers_mssql, "run_exec", fake_run_exec)
  monkeypatch.setattr(users_providers_mssql, "run_json_one", fake_run_json_one)
  monkeypatch.setattr(users_providers_mssql, "get_auth_provider_recid", fake_get_auth_provider_recid)

  args = {
    "provider": "microsoft",
    "provider_identifier": str(uuid4()),
    "provider_email": "user@example.com",
    "provider_displayname": "User",
    "provider_profile_image": "img",
  }
  res = asyncio.run(users_providers_mssql.create_from_provider_v1(args))

  assert any("insert into users_profileimg" in sql for sql in executed)
  assert any("insert into users_roles" in sql for sql in executed)
  assert res.rows
  assert res.rows[0]["profile_image"] == "img"

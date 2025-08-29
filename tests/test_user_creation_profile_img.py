import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from server.modules.providers.database.mssql_provider import registry
from server.modules.providers import DBResult


def test_create_from_provider_inserts_profile_image(monkeypatch):
  executed = []

  class DummyCursor:
    async def execute(self, sql, params):
      executed.append(sql.lower())

  @asynccontextmanager
  async def dummy_transaction():
    yield DummyCursor()

  async def fake_fetch_json(query, params, many=False):
    q = query.strip().lower()
    if q.startswith("select recid from auth_providers"):
      return DBResult(rows=[{"recid": 1}], rowcount=1)
    return DBResult(rows=[{"guid": "gid", "profile_image": args["provider_profile_image"]}], rowcount=1)

  async def fake_fetch_rows(query, params, one=False, stream=False):
    return DBResult(rows=[{"guid": "gid", "profile_image": args["provider_profile_image"]}], rowcount=1)

  monkeypatch.setattr(registry, "transaction", dummy_transaction)
  monkeypatch.setattr(registry, "fetch_json", fake_fetch_json)
  monkeypatch.setattr(registry, "fetch_rows", fake_fetch_rows)

  handler = registry.get_handler("urn:users:providers:create_from_provider:1")
  args = {
    "provider": "microsoft",
    "provider_identifier": str(uuid4()),
    "provider_email": "user@example.com",
    "provider_displayname": "User",
    "provider_profile_image": "img",
  }
  res = asyncio.run(handler(args))

  assert any("insert into users_profileimg" in sql for sql in executed)
  assert any("insert into users_roles" in sql for sql in executed)
  assert res.rows
  assert res.rows[0]["profile_image"] == "img"


import json, asyncpg, logging
from uuid import UUID, uuid4
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvironmentModule

def _maybe_loads_json(data):
  if isinstance(data, str):
    try:
      return json.loads(data)
    except ValueError:
      return data
  if isinstance(data, asyncpg.Record):
    return {k: _maybe_loads_json(v) for k, v in data.items()}
  if isinstance(data, list):
    return [_maybe_loads_json(v) for v in data]
  return data

def _stou(value: str) -> UUID:
  return UUID(value)

def _utos(value: UUID) -> str:
  return str(value)

class DatabaseModule(BaseModule):
  def __init__(self, app: FastAPI, dsn: str | None = None):
    super().__init__(app)
    self.pool: asyncpg.Pool | None = None
    self.dsn = dsn

  def _db_connection_string(self) -> str | None:
    if self.dsn:
      return self.dsn
    env: EnvironmentModule | None = getattr(self.app.state, 'env', None)
    if env:
      return env.get("POSTGRES_CONNECTION_STRING")
    return None

  async def startup(self):
    dsn = self._db_connection_string()
    if dsn:
      self.pool = await asyncpg.create_pool(dsn=dsn)
      logging.info("Database module loaded")

  async def shutdown(self):
    if self.pool:
      await self.pool.close()
      self.pool = None
    logging.info("Database module shutdown")

  async def _fetch_many(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      result = await conn.fetch(query, *args)
    return _maybe_loads_json(result)

  async def _fetch_one(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      result = await conn.fetchrow(query, *args)
    return _maybe_loads_json(result)

  async def _run(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      await conn.execute(query, *args)

  async def select_user(self, provider: str, provider_user_id: str):
    logging.debug(
      "select_user provider=%s provider_user_id=%s",
      provider,
      provider_user_id,
    )
    query = """
      SELECT
        u.guid,
        u.display_name,
        u.email,
        COALESCE(uc.credits, 0) AS credits,
        ap.name AS provider_name
      FROM users u
      JOIN users_auth ua ON ua.user_guid = u.guid
      JOIN auth_provider ap ON ap.id = ua.provider_id
      LEFT JOIN users_credits uc ON uc.user_guid = u.guid
      WHERE ap.name = $1 AND ua.provider_user_id = $2;
    """
    result = await self._fetch_one(query, provider, provider_user_id)
    if result:
      logging.info(
        f"Found {result['provider_name']} user for {result['guid']}: "
        f"{result.get('display_name')}, {result['email']}, Credits: {result['credits']}"
      )
    return result

  async def insert_user(self, provider: str, provider_user_id: str, email: str, username: str):
    logging.debug(
      "insert_user provider=%s provider_user_id=%s email=%s username=%s",
      provider,
      provider_user_id,
      email,
      username,
    )
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    new_guid = _utos(uuid4())
    async with self.pool.acquire() as conn:
      async with conn.transaction():
        auth_provider_id = await conn.fetchval(
          "SELECT id FROM auth_provider WHERE name = $1",
          provider
        )
        if not auth_provider_id:
          raise ValueError(f"Unknown auth provider: {provider}")

        await conn.execute(
          "INSERT INTO users (guid, email, display_name, auth_provider) VALUES ($1, $2, $3, $4)",
          new_guid,
          email,
          username,
          auth_provider_id,
        )

        await conn.execute(
          "INSERT INTO users_auth (user_guid, provider_id, provider_user_id) VALUES ($1, $2, $3)",
          new_guid,
          auth_provider_id,
          provider_user_id,
        )

        await conn.execute(
          "INSERT INTO users_credits (user_guid, credits) VALUES ($1, 50)",
          new_guid,
        )
    return await self.select_user(provider, provider_user_id)

  async def select_routes(self):
    logging.debug("select_routes")
    query = "SELECT * FROM routes ORDER BY sequence ASC;"
    result = await self._fetch_many(query)
    if result:
      names = ", ".join(route.get("name", "Unnamed") for route in result)
      logging.info(
        "Returning %d routes: %s", len(result), names
      )
    return result

  async def select_links(self):
    logging.debug("select_links")
    query = "SELECT * FROM links;"
    result = await self._fetch_many(query)
    if result:
      titles = ", ".join(link.get("title", "Untitled") for link in result)
      logging.inf(
        "Returning %d routes: %s", len(result), titles
      )
    return result

  async def get_config_value(self, key: str) -> str | None:
    logging.debug("get_config_value key=%s", key)
    query = "SELECT value FROM config WHERE key=$1;"
    row = await self._fetch_one(query, key)
    if row:
      return row.get("value")
    return None

  async def set_config_value(self, key: str, value: str):
    logging.debug("set_config_value key=%s", key)
    query = (
      "INSERT INTO configuration(key, value) VALUES($1, $2) "
      "ON CONFLICT(key) DO UPDATE SET value=excluded.value;"
    )
    await self._run(query, key, value)
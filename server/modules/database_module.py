import json, asyncpg, logging
from uuid import UUID, uuid4
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvironmentModule
from .discord_module import DiscordModule

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
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.pool: asyncpg.Pool | None = None
    try:
      self.env: EnvironmentModule = app.state.env
      self.discord: DiscordModule = app.state.discord
    except AttributeError:
      raise Exception("Env and Discord modules must be loaded first")

  def _db_connection_string(self) -> str | None:
    if self.env:
      return self.env.get("POSTGRES_CONNECTION_STRING")
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
      result = await conn.fetchval(query, *args)
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

  async def _secure_fetch_many(self, query: str, sub: str, *args):
    sub_uuid = _stou(sub)
    return await self._fetch_many(query, sub_uuid, *args)

  async def _secure_fetch_one(self, query: str, sub: str, *args):
    sub_uuid = _stou(sub)
    return await self._fetch_one(query, sub_uuid, *args)

  async def _secure_run(self, query: str, sub: str, *args):
    sub_uuid = _stou(sub)
    await self._run(query, sub_uuid, *args)

  async def select_user(self, provider: str, provider_user_id: str):
    logging.info(
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
        $2::text AS provider_name
      FROM users u
      JOIN users_auth ua ON ua.user_guid = u.guid
      LEFT JOIN users_credits uc ON uc.user_guid = u.guid
      WHERE ua.microsoft_id = $1;
    """
    result = await self._fetch_one(query, provider_user_id, provider)
    if result:
      logging.info(
        f"Found {result['provider_name']} user for {result['guid']}: "
        f"{result.get('display_name')}, {result['email']}, Credits: {result['credits']}"
      )
    return result

  async def insert_user(self, provider: str, provider_user_id: str, email: str, username: str):
    logging.info(
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
        await conn.execute(
          "INSERT INTO users (guid, email, display_name, auth_provider) VALUES ($1, $2, $3, $4)",
          new_guid,
          email,
          username,
          1,
        )
        await conn.execute(
          "INSERT INTO users_auth (user_guid, microsoft_id) VALUES ($1, $2)",
          new_guid,
          provider_user_id,
        )
        await conn.execute(
          "INSERT INTO users_credits (user_guid, credits) VALUES ($1, 50)",
          new_guid,
        )
    return await self.select_user(provider, provider_user_id)


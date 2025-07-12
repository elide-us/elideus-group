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

  async def select_ms_user(self, microsoft_id: str):
    query = """
      SELECT 
        u.guid,
        u.microsoft_id,
        u.email,
        u.username,
        u.backup_email,
        u.credits,
        p.name AS provider_name
      FROM users u
      JOIN auth_provider p ON u.default_provider = p.id
      WHERE u.microsoft_id = $1;
    """
    return await self._fetch_one(query, microsoft_id)

  async def insert_ms_user(self, microsoft_id: str, email: str, username: str):
    new_uuid = _utos(uuid4())
    query = """
      INSERT INTO users (guid, microsoft_id, email, username, security, credits)
      VALUES ($1, $2, $3, $4, 1, 50);
    """
    await self._run(query, new_uuid, microsoft_id, email, username)
    return await self.select_ms_user(microsoft_id)

  async def select_user_details(self, sub: str):
    query = """
      SELECT u.username, u.email, u.backup_email, u.credits, ap.name AS provider_name
      FROM users u
      LEFT JOIN auth_provider ap ON u.default_provider = ap.id
      WHERE u.guid = $1
    """
    result = await self._secure_fetch_one(query, sub)
    return {
      "guid": sub,
      "username": result.get("username", "No user found"),
      "email": result.get("email", "No email found"),
      "backup_email": result.get("backup_email", "No backup email found"),
      "credits": result.get("credits", 0),
      "default_provider": result.get("provider_name", "No provider found"),
    }

  async def select_user_security(self, sub: str):
    query = """
      SELECT security, guid FROM users WHERE guid = $1
    """
    result = await self._secure_fetch_one(query, sub)
    return {"guid": sub, "security": result["security"]}

  async def select_public_routes(self):
    query = """
      SELECT json_agg(
        json_build_object('path', path, 'name', name, 'icon', icon)
      ) AS routes
      FROM (
        SELECT path, name, icon 
        FROM routes 
        WHERE security < 1 
        ORDER BY sequence) subquery;
    """
    return await self._fetch_many(query)

  async def select_secure_routes(self, sub: str):
    query = """
      SELECT json_agg(
        json_build_object(
          'path', r.path,
          'name', r.name,
          'icon', r.icon
        )
      ) AS routes
      FROM (
        SELECT r.path, r.name, r.icon
        FROM routes r
        JOIN users u ON u.guid = $1
        WHERE r.security < u.security
        ORDER BY r.sequence
      ) subquery;
    """
    return await self._secure_fetch_many(query, sub)

  async def update_user_credits(self, amount: int, sub: str):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    sub_uuid = _stou(sub)
    query_select = "SELECT credits FROM users WHERE guid = $1"
    query_update = "UPDATE users SET credits = $1 WHERE guid = $2"
    async with self.pool.acquire() as conn:
      async with conn.transaction():
        result = await conn.fetchrow(query_select, sub_uuid)
        if result:
          credits = result["credits"]
          if credits >= amount:
            new_credits = credits - amount
            await conn.execute(query_update, new_credits, sub_uuid)
            return {"success": True, "guid": sub, "credits": new_credits}
          else:
            return {
              "success": False,
              "guid": sub,
              "credits": credits,
              "error": "Insufficient credits",
            }
        else:
          return {"success": False, "guid": sub, "error": "User not found"}

  async def update_user_credits_purchased(self, amount: int, sub: str):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    sub_uuid = _stou(sub)
    query_select = "SELECT credits FROM users WHERE guid = $1"
    query_update = "UPDATE users SET credits = $1 WHERE guid = $2"
    async with self.pool.acquire() as conn:
      async with conn.transaction():
        result = await conn.fetchrow(query_select, sub_uuid)
        if result:
          credits = result["credits"]
          new_credits = credits + amount
          await conn.execute(query_update, new_credits, sub_uuid)
          return {"success": True, "guid": sub, "credits": new_credits}
        else:
          return {"success": False, "guid": sub, "error": "User not found"}


import json, asyncpg, logging
from uuid import UUID, uuid4
from datetime import datetime
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
        ap.name AS provider_name,
        upi.image_b64 AS profile_image
      FROM users u
      JOIN users_auth ua ON ua.user_guid = u.guid
      JOIN auth_provider ap ON ap.id = ua.provider_id
      LEFT JOIN users_credits uc ON uc.user_guid = u.guid
      LEFT JOIN users_profileimg upi ON upi.user_guid = u.guid
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

  async def get_user_profile(self, guid: str):
    logging.debug("get_user_profile guid=%s", guid)
    query = """
      SELECT
        u.guid,
        u.display_name,
        u.email,
        u.display_email,
        u.rotation_token,
        u.rotation_expires,
        COALESCE(uc.credits, 0) AS credits,
        ap.name AS provider_name,
        upi.image_b64 AS profile_image
      FROM users u
      LEFT JOIN users_credits uc ON uc.user_guid = u.guid
      LEFT JOIN users_auth ua ON ua.user_guid = u.guid
      LEFT JOIN auth_provider ap ON ap.id = ua.provider_id
      LEFT JOIN users_profileimg upi ON upi.user_guid = u.guid
      WHERE u.guid = $1
      LIMIT 1;
    """
    result = await self._fetch_one(query, guid)
    return result

  async def get_user_roles(self, guid: str) -> int:
    query = "SELECT roles FROM users_roles WHERE user_guid=$1;"
    row = await self._fetch_one(query, guid)
    return row.get('roles', 0) if row else 0

  async def get_user_enablements(self, guid: str) -> int:
    query = "SELECT enablements FROM users_enablements WHERE user_guid=$1;"
    row = await self._fetch_one(query, guid)
    return row.get('enablements', 0) if row else 0

  async def select_routes(self, role_mask: int = 0):
    logging.debug("select_routes role_mask=%s", role_mask)
    query = (
      "SELECT * FROM routes "
      "WHERE required_roles = 0 OR (required_roles & $1) = required_roles "
      "ORDER BY sequence ASC;"
    )
    result = await self._fetch_many(query, role_mask)
    if result:
      names = ", ".join(route.get("name", "Unnamed") for route in result)
      logging.info(
        "Returning %d routes: %s", len(result), names
      )
    return result

  async def select_links(self, role_mask: int = 0):
    logging.debug("select_links role_mask=%s", role_mask)
    query = (
      "SELECT * FROM links "
      "WHERE required_roles = 0 OR (required_roles & $1) = required_roles;"
    )
    result = await self._fetch_many(query, role_mask)
    if result:
      titles = ", ".join(link.get("title", "Untitled") for link in result)
      logging.info(
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

  async def update_display_name(self, guid: str, display_name: str):
    logging.debug("update_display_name guid=%s display_name=%s", guid, display_name)
    query = "UPDATE users SET display_name=$1 WHERE guid=$2;"
    await self._run(query, display_name, guid)

  async def select_users(self):
    query = "SELECT guid, display_name FROM users ORDER BY display_name;"
    return await self._fetch_many(query)

  async def set_user_roles(self, guid: str, roles: int):
    query = (
      "INSERT INTO users_roles(user_guid, roles) VALUES($1, $2) "
      "ON CONFLICT(user_guid) DO UPDATE SET roles=excluded.roles;"
    )
    await self._run(query, guid, roles)

  async def set_user_credits(self, guid: str, credits: int):
    query = (
      "INSERT INTO users_credits(user_guid, credits) VALUES($1, $2) "
      "ON CONFLICT(user_guid) DO UPDATE SET credits=excluded.credits;"
    )
    await self._run(query, guid, credits)

  async def set_user_rotation_token(self, guid: str, token: str, expires: datetime):
    query = "UPDATE users SET rotation_token=$1, rotation_expires=$2 WHERE guid=$3;"
    await self._run(query, token, expires, guid)

  async def create_user_session(self, user_guid: str, bearer: str, rotation: str, expires: datetime) -> str:
    session_id = _utos(uuid4())
    await self._run("DELETE FROM user_sessions WHERE user_guid=$1", user_guid)
    query = (
      "INSERT INTO user_sessions(session_id, user_guid, bearer_token, rotation_token, created_at, expires_at) "
      "VALUES($1, $2, $3, $4, NOW(), $5);"
    )
    await self._run(query, session_id, user_guid, bearer, rotation, expires)
    return session_id

  async def get_session_by_rotation(self, rotation_token: str):
    query = "SELECT * FROM user_sessions WHERE rotation_token=$1;"
    return await self._fetch_one(query, rotation_token)

  async def update_session_tokens(self, session_id: str, bearer: str, rotation: str, expires: datetime):
    query = (
      "UPDATE user_sessions SET bearer_token=$2, rotation_token=$3, expires_at=$4 "
      "WHERE session_id=$1;"
    )
    await self._run(query, session_id, bearer, rotation, expires)

  async def delete_session(self, session_id: str):
    await self._run("DELETE FROM user_sessions WHERE session_id=$1", session_id)

  async def get_user_profile_image(self, guid: str) -> str | None:
    query = "SELECT image_b64 FROM users_profileimg WHERE user_guid=$1;"
    row = await self._fetch_one(query, guid)
    if row:
      return row.get('image_b64')
    return None

  async def set_user_profile_image(self, guid: str, image_b64: str):
    query = (
      "INSERT INTO users_profileimg(user_guid, image_b64) VALUES($1, $2) "
      "ON CONFLICT(user_guid) DO UPDATE SET image_b64=excluded.image_b64;"
    )
    await self._run(query, guid, image_b64)

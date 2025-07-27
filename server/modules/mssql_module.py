import json, aioodbc, logging
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
  if isinstance(data, dict):
    return {k: _maybe_loads_json(v) for k, v in data.items()}
  if isinstance(data, list):
    return [_maybe_loads_json(v) for v in data]
  return data

def _stou(value: str) -> UUID:
  return UUID(value)

def _utos(value: UUID) -> str:
  return str(value)

class MSSQLModule(BaseModule):
  def __init__(self, app: FastAPI, dsn: str | None = None):
    super().__init__(app)
    self.pool: aioodbc.pool.Pool | None = None
    self.dsn = dsn

  def _db_connection_string(self) -> str | None:
    if self.dsn:
      return self.dsn
    env: EnvironmentModule | None = getattr(self.app.state, 'env', None)
    if env:
      return env.get("AZURE_SQL_CONNECTION_STRING")
    return None

  async def startup(self):
    dsn = self._db_connection_string()
    if dsn:
      self.pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
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
      async with conn.cursor() as cur:
        await cur.execute(query, args or None)
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        result = [
          {c: _maybe_loads_json(row[i]) for i, c in enumerate(cols)}
          for row in rows
        ]
    return result

  async def _fetch_one(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, args or None)
        row = await cur.fetchone()
        if not row:
          return None
        cols = [d[0] for d in cur.description]
        result = {c: _maybe_loads_json(row[i]) for i, c in enumerate(cols)}
    return result

  async def _run(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, args or None)

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
      WHERE ap.name = ? AND ua.provider_user_id = ?;
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
      async with conn.cursor() as cur:
        await cur.execute(
          "SELECT id FROM auth_provider WHERE name = ?",
          (provider,)
        )
        row = await cur.fetchone()
        auth_provider_id = row[0] if row else None
        if not auth_provider_id:
          raise ValueError(f"Unknown auth provider: {provider}")

        await cur.execute(
          "INSERT INTO users (guid, email, display_name, auth_provider) VALUES (?, ?, ?, ?)",
          (new_guid, email, username, auth_provider_id),
        )

        await cur.execute(
          "INSERT INTO users_auth (user_guid, provider_id, provider_user_id) VALUES (?, ?, ?)",
          (new_guid, auth_provider_id, provider_user_id),
        )

        await cur.execute(
          "INSERT INTO users_credits (user_guid, credits) VALUES (?, 50)",
          (new_guid,),
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
        us.rotation_token,
        us.expires_at AS rotation_expires,
        COALESCE(uc.credits, 0) AS credits,
        ap.name AS provider_name,
        upi.image_b64 AS profile_image
      FROM users u
      LEFT JOIN users_credits uc ON uc.user_guid = u.guid
      LEFT JOIN users_auth ua ON ua.user_guid = u.guid
      LEFT JOIN auth_provider ap ON ap.id = ua.provider_id
      LEFT JOIN users_profileimg upi ON upi.user_guid = u.guid
      LEFT JOIN users_sessions us ON us.user_guid = u.guid
      WHERE u.guid = ?
      LIMIT 1;
    """
    result = await self._fetch_one(query, guid)
    return result

  async def get_user_roles(self, guid: str) -> int:
    query = "SELECT roles FROM users_roles WHERE user_guid=?;"
    row = await self._fetch_one(query, guid)
    return row.get('roles', 0) if row else 0

  async def list_roles(self) -> list[dict]:
    query = "SELECT name, display, mask FROM roles ORDER BY mask;"
    return await self._fetch_many(query)

  async def set_role(self, name: str, mask: int, display: str):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      result = await conn.execute(
        "UPDATE roles SET display=?, mask=? WHERE name=?",
        name,
        display,
        mask,
      )
      if result.startswith("UPDATE 0"):
        await conn.execute(
          "INSERT INTO roles(name, display, mask) VALUES(?, ?, ?)",
          name,
          display,
          mask,
        )

  async def delete_role(self, name: str):
    await self._run("DELETE FROM roles WHERE name=?", name)

  async def get_user_enablements(self, guid: str) -> int:
    query = "SELECT enablements FROM users_enablements WHERE user_guid=?;"
    row = await self._fetch_one(query, guid)
    return row.get('enablements', 0) if row else 0

  async def select_routes(self, role_mask: int = 0):
    logging.debug("select_routes role_mask=%s", role_mask)
    query = (
      "SELECT * FROM routes "
      "WHERE required_roles = 0 OR (required_roles & ?) = required_roles "
      "ORDER BY sequence ASC;"
    )
    result = await self._fetch_many(query, role_mask)
    if result:
      names = ", ".join(route.get("name", "Unnamed") for route in result)
      logging.info(
        "Returning %d routes: %s", len(result), names
      )
    return result

  async def list_routes(self) -> list[dict]:
    query = "SELECT * FROM routes ORDER BY sequence;"
    return await self._fetch_many(query)

  async def set_route(self, path: str, name: str, icon: str, required_roles: int, sequence: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM routes WHERE path=?", (path,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE routes SET name=?, icon=?, required_roles=?, sequence=? WHERE path=?",
            (name, icon, required_roles, sequence, path),
          )
        else:
          await cur.execute(
            "INSERT INTO routes(path, name, icon, required_roles, sequence) VALUES(?, ?, ?, ?, ?)",
            (path, name, icon, required_roles, sequence),
          )

  async def delete_route(self, path: str):
    await self._run("DELETE FROM routes WHERE path=?", path)

  async def select_links(self, role_mask: int = 0):
    logging.debug("select_links role_mask=%s", role_mask)
    query = (
      "SELECT * FROM links "
      "WHERE required_roles = 0 OR (required_roles & ?) = required_roles;"
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
    query = "SELECT value FROM config WHERE key=?;"
    row = await self._fetch_one(query, key)
    if row:
      return row.get("value")
    return None

  async def set_config_value(self, key: str, value: str):
    logging.debug("set_config_value key=%s", key)
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(
          "UPDATE config SET value=? WHERE key=?",
          (value, key),
        )
        if cur.rowcount == 0:
          await cur.execute(
            "INSERT INTO config(key, value) VALUES(?, ?)",
            (key, value),
          )

  async def list_config(self) -> list[dict]:
    query = "SELECT key, value FROM config ORDER BY key;"
    return await self._fetch_many(query)

  async def delete_config_value(self, key: str):
    await self._run("DELETE FROM config WHERE key=?", key)

  async def update_display_name(self, guid: str, display_name: str):
    logging.debug("update_display_name guid=%s display_name=%s", guid, display_name)
    query = "UPDATE users SET display_name=? WHERE guid=?;"
    await self._run(query, display_name, guid)

  async def select_users(self):
    query = "SELECT guid, display_name FROM users ORDER BY display_name;"
    return await self._fetch_many(query)

  async def select_users_with_role(self, mask: int):
    query = (
      "SELECT u.guid, u.display_name FROM users u "
      "JOIN users_roles ur ON u.guid = ur.user_guid "
      "WHERE (ur.roles & ?) = ? ORDER BY u.display_name;"
    )
    return await self._fetch_many(query, mask, mask)

  async def select_users_without_role(self, mask: int):
    query = (
      "SELECT u.guid, u.display_name FROM users u "
      "LEFT JOIN users_roles ur ON u.guid = ur.user_guid "
      "WHERE ur.roles IS NULL OR (ur.roles & ?) = 0 "
      "ORDER BY u.display_name;"
    )
    return await self._fetch_many(query, mask)

  async def set_user_roles(self, guid: str, roles: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_roles WHERE user_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_roles SET roles=? WHERE user_guid=?",
            (roles, guid),
          )
        else:
          await cur.execute(
            "INSERT INTO users_roles(user_guid, roles) VALUES(?, ?)",
            (guid, roles),
          )

  async def set_user_credits(self, guid: str, credits: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_credits WHERE user_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_credits SET credits=? WHERE user_guid=?",
            (credits, guid),
          )
        else:
          await cur.execute(
            "INSERT INTO users_credits(user_guid, credits) VALUES(?, ?)",
            (guid, credits),
          )

  async def set_user_rotation_token(self, guid: str, token: str, expires: datetime):
    query = (
      "UPDATE users_sessions SET rotation_token=?, expires_at=? "
      "WHERE user_guid=?;"
    )
    await self._run(query, token, expires, guid)

  async def create_user_session(self, user_guid: str, bearer: str, rotation: str, expires: datetime) -> str:
    session_id = _utos(uuid4())
    await self._run("DELETE FROM users_sessions WHERE user_guid=?", user_guid)
    query = (
      "INSERT INTO users_sessions(session_id, user_guid, bearer_token, rotation_token, created_at, expires_at) "
      "VALUES(?, ?, ?, ?, GETDATE(), ?);"
    )
    await self._run(query, session_id, user_guid, bearer, rotation, expires)
    return session_id

  async def get_session_by_rotation(self, rotation_token: str):
    query = "SELECT * FROM users_sessions WHERE rotation_token=?;"
    return await self._fetch_one(query, rotation_token)

  async def update_session_tokens(self, session_id: str, bearer: str, rotation: str, expires: datetime):
    query = (
      "UPDATE users_sessions SET bearer_token=?, rotation_token=?, expires_at=? "
      "WHERE session_id=?;"
    )
    await self._run(query, session_id, bearer, rotation, expires)

  async def delete_session(self, session_id: str):
    await self._run("DELETE FROM users_sessions WHERE session_id=?", session_id)

  async def get_user_profile_image(self, guid: str) -> str | None:
    query = "SELECT image_b64 FROM users_profileimg WHERE user_guid=?;"
    row = await self._fetch_one(query, guid)
    if row:
      return row.get('image_b64')
    return None

  async def set_user_profile_image(self, guid: str, image_b64: str):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_profileimg WHERE user_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_profileimg SET image_b64=? WHERE user_guid=?",
            (image_b64, guid),
          )
        else:
          await cur.execute(
            "INSERT INTO users_profileimg(user_guid, image_b64) VALUES(?, ?)",
            (guid, image_b64),
          )

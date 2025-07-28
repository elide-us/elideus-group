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
        if args:
          await cur.execute(query, args)
        else:
          await cur.execute(query)
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
        if args:
          await cur.execute(query, args)
        else:
          await cur.execute(query)
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
        if args:
          await cur.execute(query, args)
        else:
          await cur.execute(query)

  async def select_user(self, provider: str, provider_user_id: str):
    logging.debug(
      "select_user provider=%s provider_user_id=%s",
      provider,
      provider_user_id,
    )
    query = """
      SELECT
        u.element_guid AS guid,
        u.element_display AS display_name,
        u.element_email AS email,
        COALESCE(uc.element_credits, 0) AS credits,
        ap.element_name AS provider_name,
        upi.element_base64 AS profile_image
      FROM account_users u
      JOIN users_auth ua ON ua.users_guid = u.element_guid
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      LEFT JOIN users_credits uc ON uc.users_guid = u.element_guid
      LEFT JOIN users_profileimg upi ON upi.users_guid = u.element_guid
      WHERE ap.element_name = ? AND ua.element_identifier = ?;
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
          "SELECT recid FROM auth_providers WHERE element_name = ?",
          (provider,)
        )
        row = await cur.fetchone()
        auth_provider_id = row[0] if row else None
        if not auth_provider_id:
          raise ValueError(f"Unknown auth provider: {provider}")

        await cur.execute(
          "INSERT INTO account_users (element_guid, element_email, element_display, providers_recid) VALUES (?, ?, ?, ?)",
          (new_guid, email, username, auth_provider_id),
        )

        await cur.execute(
          "INSERT INTO users_auth (users_guid, providers_recid, element_identifier) VALUES (?, ?, ?)",
          (new_guid, auth_provider_id, provider_user_id),
        )

        await cur.execute(
          "INSERT INTO users_credits (users_guid, element_credits) VALUES (?, 50)",
          (new_guid,),
        )
    return await self.select_user(provider, provider_user_id)

  async def get_user_profile(self, guid: str):
    logging.debug("get_user_profile guid=%s", guid)
    query = """
      SELECT
        u.element_guid AS guid,
        u.element_display AS display_name,
        u.element_email AS email,
        u.element_optin AS display_email,
        us.element_token AS rotation_token,
        us.element_token_exp AS rotation_expires,
        COALESCE(uc.element_credits, 0) AS credits,
        ap.element_name AS provider_name,
        upi.element_base64 AS profile_image
      FROM account_users u
      LEFT JOIN users_credits uc ON uc.users_guid = u.element_guid
      LEFT JOIN users_auth ua ON ua.users_guid = u.element_guid
      LEFT JOIN auth_providers ap ON ap.recid = ua.providers_recid
      LEFT JOIN users_profileimg upi ON upi.users_guid = u.element_guid
      LEFT JOIN users_sessions us ON us.users_guid = u.element_guid
      WHERE u.element_guid = ?
      LIMIT 1;
    """
    result = await self._fetch_one(query, guid)
    return result

  async def get_user_roles(self, guid: str) -> int:
    query = "SELECT element_roles FROM users_roles WHERE users_guid=?;"
    row = await self._fetch_one(query, guid)
    return row.get('element_roles', 0) if row else 0

  async def list_roles(self) -> list[dict]:
    query = "SELECT element_name AS name, element_display AS display, element_mask AS mask FROM system_roles ORDER BY element_mask;"
    return await self._fetch_many(query)

  async def set_role(self, name: str, mask: int, display: str):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      result = await conn.execute(
        "UPDATE system_roles SET element_display=?, element_mask=? WHERE element_name=?",
        name,
        display,
        mask,
      )
      if result.startswith("UPDATE 0"):
        await conn.execute(
          "INSERT INTO system_roles(element_name, element_display, element_mask) VALUES(?, ?, ?)",
          name,
          display,
          mask,
        )

  async def delete_role(self, name: str):
    await self._run("DELETE FROM system_roles WHERE element_name=?", name)

  async def get_user_enablements(self, guid: str) -> int:
    query = "SELECT element_enablements FROM users_enablements WHERE users_guid=?;"
    row = await self._fetch_one(query, guid)
    return row.get('element_enablements', 0) if row else 0

  async def select_routes(self, role_mask: int = 0):
    logging.debug("select_routes role_mask=%s", role_mask)
    query = (
      "SELECT * FROM frontend_routes "
      "WHERE element_roles = 0 OR (element_roles & ?) = element_roles "
      "ORDER BY element_sequence ASC;"
    )
    result = await self._fetch_many(query, role_mask)
    if result:
      names = ", ".join(route.get("element_name", "Unnamed") for route in result)
      logging.info(
        "Returning %d routes: %s", len(result), names
      )
    return result

  async def list_routes(self) -> list[dict]:
    query = "SELECT * FROM frontend_routes ORDER BY element_sequence;"
    return await self._fetch_many(query)

  async def set_route(self, path: str, name: str, icon: str, required_roles: int, sequence: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM frontend_routes WHERE element_path=?", (path,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE frontend_routes SET element_name=?, element_icon=?, element_roles=?, element_sequence=? WHERE element_path=?",
            (name, icon, required_roles, sequence, path),
          )
        else:
          await cur.execute(
            "INSERT INTO frontend_routes(element_path, element_name, element_icon, element_roles, element_sequence) VALUES(?, ?, ?, ?, ?)",
            (path, name, icon, required_roles, sequence),
          )

  async def delete_route(self, path: str):
    await self._run("DELETE FROM frontend_routes WHERE element_path=?", path)

  async def select_links(self, role_mask: int = 0):
    logging.debug("select_links role_mask=%s", role_mask)
    query = "SELECT * FROM frontend_links ORDER BY element_sequence;"
    result = await self._fetch_many(query)
    if result:
      titles = ", ".join(link.get("element_title", "Untitled") for link in result)
      logging.info(
        "Returning %d routes: %s", len(result), titles
      )
    return result

  async def get_config_value(self, key: str) -> str | None:
    logging.debug("get_config_value key=%s", key)
    query = "SELECT element_value FROM system_config WHERE element_key=?;"
    row = await self._fetch_one(query, key)
    if row:
      return row.get("element_value")
    return None

  async def set_config_value(self, key: str, value: str):
    logging.debug("set_config_value key=%s", key)
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(
          "UPDATE system_config SET element_value=? WHERE element_key=?",
          (value, key),
        )
        if cur.rowcount == 0:
          await cur.execute(
            "INSERT INTO system_config(element_key, element_value) VALUES(?, ?)",
            (key, value),
          )

  async def list_config(self) -> list[dict]:
    query = "SELECT element_key, element_value FROM system_config ORDER BY element_key;"
    return await self._fetch_many(query)

  async def delete_config_value(self, key: str):
    await self._run("DELETE FROM system_config WHERE element_key=?", key)

  async def update_display_name(self, guid: str, display_name: str):
    logging.debug("update_display_name guid=%s display_name=%s", guid, display_name)
    query = "UPDATE account_users SET element_display=? WHERE element_guid=?;"
    await self._run(query, display_name, guid)

  async def select_users(self):
    query = "SELECT element_guid AS guid, element_display AS display_name FROM account_users ORDER BY element_display;"
    return await self._fetch_many(query)

  async def select_users_with_role(self, mask: int):
    query = (
      "SELECT u.element_guid AS guid, u.element_display AS display_name FROM account_users u "
      "JOIN users_roles ur ON u.element_guid = ur.users_guid "
      "WHERE (ur.element_roles & ?) = ? ORDER BY u.element_display;"
    )
    return await self._fetch_many(query, mask, mask)

  async def select_users_without_role(self, mask: int):
    query = (
      "SELECT u.element_guid AS guid, u.element_display AS display_name FROM account_users u "
      "LEFT JOIN users_roles ur ON u.element_guid = ur.users_guid "
      "WHERE ur.element_roles IS NULL OR (ur.element_roles & ?) = 0 "
      "ORDER BY u.element_display;"
    )
    return await self._fetch_many(query, mask)

  async def set_user_roles(self, guid: str, roles: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_roles WHERE users_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_roles SET element_roles=? WHERE users_guid=?",
            (roles, guid),
          )
        else:
          await cur.execute(
            "INSERT INTO users_roles(users_guid, element_roles) VALUES(?, ?)",
            (guid, roles),
          )

  async def set_user_credits(self, guid: str, credits: int):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_credits WHERE users_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_credits SET element_credits=? WHERE users_guid=?",
            (credits, guid),
          )
        else:
          await cur.execute(
            "INSERT INTO users_credits(users_guid, element_credits) VALUES(?, ?)",
            (guid, credits),
          )

  async def set_user_rotation_token(self, guid: str, token: str, expires: datetime):
    query = (
      "UPDATE users_sessions SET element_token=?, element_token_exp=? "
      "WHERE users_guid=?;"
    )
    await self._run(query, token, expires, guid)

  async def create_user_session(self, user_guid: str, bearer: str, rotation: str, expires: datetime) -> str:
    session_id = _utos(uuid4())
    await self._run("DELETE FROM users_sessions WHERE users_guid=?", user_guid)
    query = (
      "INSERT INTO users_sessions(element_guid, users_guid, element_token, element_token_iat, element_token_exp) "
      "VALUES(?, ?, ?, GETDATE(), ?);"
    )
    await self._run(query, session_id, user_guid, rotation, expires)
    return session_id

  async def get_session_by_rotation(self, rotation_token: str):
    query = "SELECT * FROM users_sessions WHERE element_token=?;"
    return await self._fetch_one(query, rotation_token)

  async def update_session_tokens(self, session_id: str, bearer: str, rotation: str, expires: datetime):
    query = (
      "UPDATE users_sessions SET element_token=?, element_token_exp=? "
      "WHERE element_guid=?;"
    )
    await self._run(query, rotation, expires, session_id)

  async def delete_session(self, session_id: str):
    await self._run("DELETE FROM users_sessions WHERE element_guid=?", session_id)

  async def get_user_profile_image(self, guid: str) -> str | None:
    query = "SELECT element_base64 FROM users_profileimg WHERE users_guid=?;"
    row = await self._fetch_one(query, guid)
    if row:
      return row.get('element_base64')
    return None

  async def set_user_profile_image(self, guid: str, image_b64: str, provider: str | None = None):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM users_profileimg WHERE users_guid=?", (guid,))
        row = await cur.fetchone()
        if row:
          await cur.execute(
            "UPDATE users_profileimg SET element_base64=? WHERE users_guid=?",
            (image_b64, guid),
          )
        else:
          provider_id = None
          if provider:
            await cur.execute(
              "SELECT recid FROM auth_providers WHERE element_name=?",
              (provider,)
            )
            prow = await cur.fetchone()
            provider_id = prow[0] if prow else None
          if not provider_id:
            await cur.execute(
              "SELECT providers_recid FROM account_users WHERE element_guid=?",
              (guid,)
            )
            prow = await cur.fetchone()
            provider_id = prow[0] if prow else None
          if provider_id is None:
            raise ValueError("Unknown auth provider for user")
          await cur.execute(
            "INSERT INTO users_profileimg(users_guid, element_base64, providers_recid) VALUES(?, ?, ?)",
            (guid, image_b64, provider_id),
          )

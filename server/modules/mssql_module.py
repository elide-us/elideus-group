import os, json, aioodbc, logging
from contextlib import asynccontextmanager
from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import FastAPI
from . import BaseModule
from .env_module import EnvModule

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

DEFAULT_STARTING_CREDITS = 50

class MSSQLModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.pool: aioodbc.pool.Pool | None = None

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()

    dsn = env.get("AZURE_SQL_CONNECTION_STRING")
    self.pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
    logging.info("MSSQL ODBC Connection Pool Created")

    self.mark_ready()
    
  async def shutdown(self):
    if self.pool:
      await self.pool.close()
      self.pool = None
    logging.info("MSSQL ODBC Connection Pool Closed")

  @asynccontextmanager
  async def _transaction(self):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cur:
        try:
          await conn.begin()
          yield cur
          await conn.commit()
        except Exception as e:
          await conn.rollback()
          logging.debug(f"[TRANSACTION ERROR] Rolled back due to: {e}")
          raise

  async def _fetch_json(self, query: str, *args):
    if not self.pool:
      raise RuntimeError("Database pool not initialized")
    try:
      async with self.pool.acquire() as conn:
        async with conn.cursor() as cur:
          await cur.execute(query, args or ())
          row = await cur.fetchone()
          if not row or not row[0]:
            return None
          return json.loads(row[0])
    except Exception as e:
      logging.debug(f"Query failed:\n{query}\nArgs: {args}\nError: {e}")
      return None

  ## DEPRECATED ##
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

  ## DEPRECATED ##
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
    try:
      async with self.pool.acquire() as conn:
        async with conn.cursor() as cur:
          await cur.execute(query, args or ())
      return True
    except Exception as e:
      logging.debug(f"Query failed:\n{query}\nArgs: {args}\nError: {e}")
      return False

################################################################################

  async def select_user(self, provider: str, provider_identifier: str):
    query = """
      SELECT
        u.element_guid AS guid,
        u.element_display AS display_name,
        u.element_email AS email,
        COALESCE(uc.element_credits, 0) AS credits,
        ap.element_name AS provider_name,
        ap.element_display AS provider_display,
        upi.element_base64 AS profile_image
      FROM account_users u
      JOIN users_auth ua ON ua.users_guid = u.element_guid
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      LEFT JOIN users_credits uc ON uc.users_guid = u.element_guid
      LEFT JOIN users_profileimg upi ON upi.users_guid = u.element_guid
      WHERE ap.element_name = ? AND ua.element_identifier = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    result = await self._fetch_json(query, provider, provider_identifier)
    if result:
      logging.info(
        f"Found {result['provider_display']} user for {result['guid']}: "
        f"{result['display_name']}, {result['email']}, Credits: {result['credits']}"
      )
    return result
  
  async def insert_user(self, provider: str, provider_identifier: str, provider_email: str, provider_displayname: str):
    new_guid = _utos(uuid4())
    element_rotkey = ""
    element_rotkey_iat = datetime.now(timezone.utc)
    element_rotkey_exp = datetime.now(timezone.utc)
    row = await self._fetch_json(
      "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;", provider
    )
    if not row:
      raise ValueError(f"Unknown auth provider: {provider}")
    auth_provider_id = row["recid"]
    async with self._transaction() as cur:
      await cur.execute(
        """
        INSERT INTO account_users (element_guid, element_email, element_display, providers_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
        VALUES (?, ?, ?, ?);
        """,
        (new_guid, provider_email, provider_displayname, auth_provider_id, element_rotkey, element_rotkey_iat, element_rotkey_exp)
      )
      await cur.execute(
        """
        INSERT INTO users_auth (users_guid, providers_recid, element_identifier)
        VALUES (?, ?, ?);
        """,
        (new_guid, auth_provider_id, provider_identifier)
      )
      await cur.execute(
        """
        INSERT INTO users_credits (users_guid, element_credits)
        VALUES (?, ?);
        """,
        (new_guid, DEFAULT_STARTING_CREDITS)
      )

    return await self.select_user(provider, provider_identifier)

  async def get_user_profile(self, guid: str):
    query = """
      SELECT TOP 1
        u.element_guid AS guid,
        u.element_display AS display_name,
        u.element_email AS email,
        u.element_optin AS display_email,
        COALESCE(uc.element_credits, 0) AS credits,
        upi.element_base64 AS profile_image,
        (
          SELECT
            ap.element_name AS name,
            ap.element_display AS display
          FROM users_auth ua
          JOIN auth_providers ap ON ap.recid = ua.providers_recid
          WHERE ua.users_guid = u.element_guid
          FOR JSON PATH
        ) AS auth_providers
      FROM account_users u
      LEFT JOIN users_credits uc ON uc.users_guid = u.element_guid
      LEFT JOIN users_profileimg upi ON upi.users_guid = u.element_guid
      WHERE u.element_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return await self._fetch_json(query, guid)

  async def get_user_roles(self, guid: str) -> int:
    query = """
      SELECT element_roles FROM users_roles
      WHERE users_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    row = await self._fetch_json(query, guid)
    return int(row['element_roles'])  # Let it blow up if it’s missing

  async def set_user_roles(self, guid: str, roles: int):
    query_update = """
      UPDATE users_roles
      SET element_roles = ?
      WHERE users_guid = ?;
    """
    query_insert = """
      INSERT INTO users_roles (users_guid, element_roles)
      VALUES (?, ?);
    """
    query_delete = """
      DELETE FROM users_roles
      WHERE users_guid = ?;
    """
    async with self._transaction() as cur:
      if roles == 0:
        await cur.execute(query_delete, (guid,))
      else:
        await cur.execute(query_update, (roles, guid))
        if cur.rowcount == 0:
          await cur.execute(query_insert, (guid, roles))

  async def get_user_routes(self, role_mask: int = 0) -> list[dict]:
    query = """
      SELECT
        element_path,
        element_name,
        element_icon,
        element_roles,
        element_sequence
      FROM frontend_routes
      WHERE element_roles = 0 OR (element_roles & ?) = element_roles
      ORDER BY element_sequence
      FOR JSON PATH;
    """
    result = await self._fetch_json(query, role_mask)
    if result:
      names = ", ".join(route.get("element_name", "Unnamed") for route in result)
      logging.info("Returning %d routes: %s", len(result), names)
    return result

  async def set_user_credits(self, guid: str, credits: int):
    query_update = """
      UPDATE users_credits
      SET element_credits = ?
      WHERE users_guid = ?;
    """
    query_insert = """
      INSERT INTO users_credits (users_guid, element_credits)
      VALUES (?, ?);
    """
    async with self._transaction() as cur:
      await cur.execute(query_update, (credits, guid))
      if cur.rowcount == 0:
        await cur.execute(query_insert, (guid, credits))

  async def update_display_name(self, guid: str, display_name: str):
    query = """
      UPDATE account_users
      SET element_display = ?
      WHERE element_guid = ?;
    """
    await self._run(query, display_name, guid)

  async def select_users(self):
    query = """
      SELECT
        element_guid AS guid,
        element_display AS display_name
      FROM account_users
      ORDER BY element_display
      FOR JSON PATH;
    """
    result = await self._fetch_json(query)
    if not result:
      raise ValueError("No users found.")
    return result

  async def select_users_with_role(self, mask: int):
    query = """
      SELECT
        u.element_guid AS guid,
        u.element_display AS display_name
      FROM account_users u
      JOIN users_roles ur ON u.element_guid = ur.users_guid
      WHERE (ur.element_roles & ?) = ?
      ORDER BY u.element_display
      FOR JSON PATH;
    """
    result = await self._fetch_json(query, mask, mask)
    if not result:
      raise ValueError(f"No users found with role mask: {mask}")
    return result

  async def select_users_without_role(self, mask: int):
    query = """
      SELECT
        u.element_guid AS guid,
        u.element_display AS display_name
      FROM account_users u
      LEFT JOIN users_roles ur ON u.element_guid = ur.users_guid
      WHERE ur.element_roles IS NULL OR (ur.element_roles & ?) = 0
      ORDER BY u.element_display
      FOR JSON PATH;
    """
    result = await self._fetch_json(query, mask)
    if not result:
      raise ValueError(f"No users found without role mask: {mask}")
    return result

  async def get_user_profile_image(self, guid: str) -> str:
    query = """
      SELECT element_base64 FROM users_profileimg
      WHERE users_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    row = await self._fetch_json(query, guid)
    if not row:
      raise ValueError(f"No profile image found for user {guid}")
    return row["element_base64"]

  async def set_user_profile_image(self, guid: str, image_b64: str):
    query_update = """
      UPDATE users_profileimg
      SET element_base64 = ?
      WHERE users_guid = ?;
    """
    query_insert = """
      INSERT INTO users_profileimg (users_guid, element_base64)
      VALUES (?, ?);
    """
    async with self._transaction() as cur:
      await cur.execute(query_update, (image_b64, guid))
      if cur.rowcount == 0:
        await cur.execute(query_insert, (guid, image_b64))

################################################################################

  async def list_roles(self):
    query = """
      SELECT
        element_name AS name,
        element_display AS display,
        element_mask AS mask
      FROM system_roles
      ORDER BY element_mask
      FOR JSON PATH;
    """
    return await self._fetch_json(query)

  async def set_role(self, name: str, mask: int, display: str):
    query_update = """
      UPDATE system_roles
      SET element_display = ?, element_mask = ?
      WHERE element_name = ?
    """
    query_insert = """
      INSERT INTO system_roles (element_name, element_display, element_mask)
      VALUES (?, ?, ?)
    """
    query_delete = """
      DELETE FROM system_roles
      WHERE element_name = ?
    """
    async with self._transaction() as cur:
      if mask == 0:
        await cur.execute(query_delete, (name,))
      else:
        await cur.execute(query_update, (display, mask, name))
        if cur.rowcount == 0:
          await cur.execute(query_insert, (name, display, mask))

################################################################################

  async def list_routes(self) -> list[dict]:
    query = """
      SELECT
        element_path,
        element_name,
        element_icon,
        element_roles,
        element_sequence
      FROM frontend_routes
      ORDER BY element_sequence
      FOR JSON PATH;
    """
    return await self._fetch_json(query)

  async def set_route(self, path: str, name: str, icon: str, roles: int, sequence: int):
    query_update = """
      UPDATE frontend_routes
      SET element_name = ?, element_icon = ?, element_roles = ?, element_sequence = ?
      WHERE element_path = ?;
    """
    query_insert = """
      INSERT INTO frontend_routes (element_path, element_name, element_icon, element_roles, element_sequence)
      VALUES (?, ?, ?, ?, ?);
    """
    query_delete = """
      DELETE FROM frontend_routes WHERE element_path = ?;
    """
    async with self._transaction() as cur:
      if roles == 0:
        await cur.execute(query_delete, (path,))
      else:
        await cur.execute(query_update, (name, icon, roles, sequence, path))
        if cur.rowcount == 0:
          await cur.execute(query_insert, (path, name, icon, roles, sequence))

################################################################################

  async def select_links(self, role_mask: int = 0):
    query = """
      SELECT
        element_title AS title,
        element_url AS url,
        element_sequence AS sequence
      FROM frontend_links
      ORDER BY element_sequence
      FOR JSON PATH;
    """
    links = await self._fetch_json(query)
    if links:
      titles = ", ".join(link.get("title", "Untitled") for link in links)
      logging.info("Returning %d links: %s", len(links), titles)
    return links

################################################################################

  async def get_config_value(self, key: str) -> str:
    query = """
      SELECT element_value FROM system_config
      WHERE element_key = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    row = await self._fetch_json(query, key)
    if not row:
      raise ValueError(f"Missing config value for key: {key}")
    return row["element_value"]

  async def set_config_value(self, key: str, value: str):
    query_update = """
      UPDATE system_config
      SET element_value = ?
      WHERE element_key = ?;
    """
    query_insert = """
      INSERT INTO system_config (element_key, element_value)
      VALUES (?, ?);
    """
    async with self._transaction() as cur:
      await cur.execute(query_update, (value, key))
      if cur.rowcount == 0:
        await cur.execute(query_insert, (key, value))

  async def list_config(self) -> list[dict]:
    query = """
      SELECT element_key, element_value FROM system_config
      ORDER BY element_key
      FOR JSON PATH;
    """
    return await self._fetch_json(query)

  async def delete_config_value(self, key: str):
    query = "DELETE FROM system_config WHERE element_key = ?;"
    await self._run(query, key)

################################################################################

  # async def set_user_rotation_token(self, guid: str, token: str, expires: datetime):
  #   query = (
  #     "UPDATE users_sessions SET element_token=?, element_token_exp=? "
  #     "WHERE users_guid=?;"
  #   )
  #   await self._run(query, token, expires, guid)

  # async def create_user_session(self, user_guid: str, bearer: str, rotation: str, expires: datetime) -> str:
  #   session_id = _utos(uuid4())
  #   await self._run("DELETE FROM users_sessions WHERE users_guid=?", user_guid)
  #   query = (
  #     "INSERT INTO users_sessions(element_guid, users_guid, element_token, element_token_iat, element_token_exp) "
  #     "VALUES(?, ?, ?, GETDATE(), ?);"
  #   )
  #   await self._run(query, session_id, user_guid, rotation, expires)
  #   return session_id

  # async def get_session_by_rotation(self, rotation_token: str):
  #   query = "SELECT * FROM users_sessions WHERE element_token=?;"
  #   return await self._fetch_one(query, rotation_token)

  # async def update_session_tokens(self, session_id: str, bearer: str, rotation: str, expires: datetime):
  #   query = (
  #     "UPDATE users_sessions SET element_token=?, element_token_exp=? "
  #     "WHERE element_guid=?;"
  #   )
  #   await self._run(query, rotation, expires, session_id)

  # async def delete_session(self, session_id: str):
  #   await self._run("DELETE FROM users_sessions WHERE element_guid=?", session_id)

  async def set_user_access_token(self, device_guid: str, token: str, expires: datetime):
    query = """
      UPDATE sessions_devices
      SET element_token = ?, element_token_exp = ?
      WHERE element_guid = ?;
    """
    await self._run(query, token, expires, device_guid)

  async def create_user_session(
    self, user_guid: str, access_token: str, expires: datetime,
    fingerprint: str | None = None, user_agent: str | None = None,
    ip_address: str | None = None
  ) -> tuple[str, str, str]:
    session_guid = _utos(uuid4())
    device_guid = _utos(uuid4())

    async with self._transaction() as cur:
      await cur.execute("""
        INSERT INTO users_sessions (element_guid, users_guid, element_created_at)
        VALUES (?, ?, SYSDATETIMEOFFSET());
      """, (session_guid, user_guid))

      await cur.execute("""
        INSERT INTO sessions_devices (
          element_guid,
          sessions_guid,
          element_token,
          element_token_iat,
          element_token_exp,
          element_device_fingerprint,
          element_user_agent,
          element_ip_last_seen
        )
        VALUES (?, ?, ?, SYSDATETIMEOFFSET(), ?, ?, ?, ?);
      """, (
        device_guid,
        session_guid,
        access_token,
        expires,
        fingerprint,
        user_agent,
        ip_address
      ))

    return session_guid, device_guid
  
  async def get_session_by_token(self, access_token: str) -> dict | None:
    query = """
      SELECT
        sd.element_guid AS device_guid,
        sd.sessions_guid AS session_guid,
        us.users_guid AS user_guid,
        sd.element_token AS token,
        sd.element_token_iat AS issued_at,
        sd.element_token_exp AS expires_at,
        sd.element_revoked_at AS revoked_at,
        sd.element_device_fingerprint AS fingerprint,
        sd.element_user_agent AS user_agent,
        sd.element_ip_last_seen AS ip
      FROM sessions_devices sd
      JOIN users_sessions us ON us.element_guid = sd.sessions_guid
      WHERE sd.element_token = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return await self._fetch_json(query, access_token)

  async def update_device_token(self, device_guid: str, access_token: str, expires: datetime):
    query = """
      UPDATE sessions_devices
      SET element_token = ?, element_token_exp = ?, element_token_iat = SYSDATETIMEOFFSET()
      WHERE element_guid = ?;
    """
    await self._run(query, access_token, expires, device_guid)

  async def delete_session(self, session_guid: str, device_guid: str):
    query_devices = "DELETE FROM sessions_devices WHERE element_guid = ?;"
    query_session = "DELETE FROM users_sessions WHERE element_guid = ?;"
    async with self._transaction() as cur:
      await cur.execute(query_devices, (device_guid,))
      await cur.execute(query_session, (session_guid,))

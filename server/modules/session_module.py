from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one
from server.modules import BaseModule
from server.modules.auth_module import (
  AuthModule,
  DEFAULT_ROTATION_TOKEN_EXPIRY,
  DEFAULT_SESSION_TOKEN_EXPIRY,
)
from server.modules.db_module import DbModule
from server.modules.oauth_module import OauthModule


class SessionModule(BaseModule):
  SESSION_TYPE_BROWSER = '184AEAD3-D35D-5882-A3C2-75BA58E6FB33'
  SESSION_TYPE_AGENT = '503A571B-2FAB-5828-AA12-E05FF018D4B7'
  SESSION_TYPE_BOT = 'A53CD0A9-C055-583B-9F84-53E54D35C1A4'
  TOKEN_TYPE_ACCESS = '8AA0F073-7CA1-5375-9989-67DB2688BDF5'
  TOKEN_TYPE_REFRESH = '8E312303-3EA8-5D6F-9341-D201D5A9ABA6'
  TOKEN_TYPE_ROTATION = 'C5551771-3FBD-5357-9302-821DE44D73B8'
  MODULE_GUID = '6D818DCB-5B60-5B80-91F1-A1D19DC03110'

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._queries: dict[str, str] = {}

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.oauth: OauthModule = self.app.state.oauth
    await self.oauth.on_ready()

    query = """
SELECT pub_name, pub_query_text
FROM system_objects_queries
WHERE ref_module_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND pub_is_active = 1
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""
    loaded = await run_json_many(query, (self.MODULE_GUID,))
    rows = loaded.rows if loaded else []
    self._queries = {
      str(row.get('pub_name')): str(row.get('pub_query_text'))
      for row in rows
      if row.get('pub_name') and row.get('pub_query_text')
    }
    logging.info('[SessionModule] Loaded %s data-driven queries', len(self._queries))
    self.mark_ready()

  async def shutdown(self):
    pass

  async def _run_query(self, query_name: str, params: tuple = ()) -> Any:
    sql = self._queries.get(query_name)
    if not sql:
      raise RuntimeError(f'Query not loaded: {query_name}')
    if 'FOR JSON' in sql:
      if 'WITHOUT_ARRAY_WRAPPER' in sql:
        return await run_json_one(sql, params)
      return await run_json_many(sql, params)
    return await run_exec(sql, params)

  def _hash_token(self, token: str) -> str:
    key = self.auth.jwt_secret.encode('utf-8')
    return hmac.new(key, token.encode('utf-8'), hashlib.sha256).hexdigest()

  def _verify_hash(self, token: str, stored_hash: str) -> bool:
    return hmac.compare_digest(self._hash_token(token), stored_hash)

  @staticmethod
  def _as_utc(value: datetime | str | None) -> datetime | None:
    if value is None:
      return None
    if isinstance(value, datetime):
      return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
      parsed = datetime.fromisoformat(value)
      return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
      return None

  @staticmethod
  def _extract_name_list(value: Any) -> list[str]:
    if not value:
      return []
    raw = value
    if isinstance(raw, str):
      try:
        raw = json.loads(raw)
      except json.JSONDecodeError:
        return [raw]
    if isinstance(raw, dict):
      raw = [raw]
    if not isinstance(raw, list):
      return []
    names: list[str] = []
    for item in raw:
      if isinstance(item, dict):
        name = item.get('name')
        if name:
          names.append(str(name))
      elif isinstance(item, str):
        names.append(item)
    return names

  async def issue_token(
    self,
    provider: str,
    id_token: str,
    access_token: str,
    fingerprint: str,
    user_agent: str | None,
    ip_address: str | None,
    confirm: bool | None = None,
    reauth_token: str | None = None,
  ) -> tuple[str, str, datetime, dict]:
    provider_uid, provider_profile, payload = await self.auth.handle_auth_login(
      provider,
      id_token,
      access_token,
    )
    user = await self.oauth.resolve_user(
      provider,
      provider_uid,
      provider_profile,
      payload,
      confirm=confirm,
      reauth_token=reauth_token,
    )

    user_guid = str(user['guid'])
    now = datetime.now(timezone.utc)
    access_expiry = now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    refresh_expiry = now + timedelta(days=DEFAULT_ROTATION_TOKEN_EXPIRY)
    rotation_token, rotation_expiry = self.auth.make_rotation_token(user_guid)

    access_placeholder = uuid.uuid4().hex
    refresh_placeholder = uuid.uuid4().hex

    created = await self._run_query(
      'security.sessions.create_session',
      (
        user_guid,
        self.SESSION_TYPE_BROWSER,
        access_expiry,
        self._hash_token(access_placeholder),
        'session',
        access_expiry,
        self._hash_token(refresh_placeholder),
        'offline_access',
        refresh_expiry,
        self._hash_token(rotation_token),
        rotation_expiry,
        fingerprint,
        user_agent,
        ip_address,
      ),
    )
    row = created.rows[0] if created and created.rows else None
    if not row:
      raise HTTPException(status_code=500, detail='Failed to create session')

    session_guid = str(row.get('session_guid'))
    device_guid = str(row.get('device_guid'))
    roles, _ = await self.auth.get_user_roles(user_guid)
    session_token, _ = self.auth.make_session_token(
      user_guid,
      rotation_token,
      session_guid,
      device_guid,
      roles,
      exp=access_expiry,
    )

    await self._run_query(
      'security.sessions.create_token',
      (
        session_guid,
        self.TOKEN_TYPE_ACCESS,
        self._hash_token(session_token),
        'session',
        access_expiry,
      ),
    )

    profile = {
      'display_name': user.get('display_name'),
      'email': user.get('email'),
      'credits': user.get('credits'),
      'profile_image': user.get('profile_image'),
    }
    return session_token, rotation_token, rotation_expiry, profile

  async def refresh_token(
    self,
    rotation_token: str,
    fingerprint: str,
    user_agent: str | None,
    ip_address: str | None,
  ) -> str:
    validated = await self._run_query(
      'security.sessions.validate_token',
      (self._hash_token(rotation_token),),
    )
    row = validated.rows[0] if validated and validated.rows else None
    if not row:
      raise HTTPException(status_code=401, detail='Invalid rotation token')

    session_guid = str(row.get('session_guid'))
    user_guid = str(row.get('user_guid'))
    token_type = str(row.get('token_type') or '')
    if token_type.lower() != 'rotation':
      raise HTTPException(status_code=401, detail='Invalid token type for refresh')

    access_expiry = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    roles, _ = await self.auth.get_user_roles(user_guid)
    session_token, _ = self.auth.make_session_token(
      user_guid,
      rotation_token,
      session_guid,
      fingerprint,
      roles,
      exp=access_expiry,
    )

    await self._run_query(
      'security.sessions.create_token',
      (
        session_guid,
        self.TOKEN_TYPE_ACCESS,
        self._hash_token(session_token),
        'session',
        access_expiry,
      ),
    )
    await self._run_query(
      'security.sessions.update_device',
      (ip_address, user_agent, session_guid),
    )
    return session_token

  async def invalidate_token(self, user_guid: str) -> None:
    query_name = 'security.sessions.list_user_sessions'
    if query_name not in self._queries:
      logging.warning('[SessionModule] Query not available for invalidate: %s', query_name)
      return
    sessions = await self._run_query(query_name, (user_guid,))
    for row in sessions.rows if sessions else []:
      session_guid = row.get('session_guid') if isinstance(row, dict) else None
      if session_guid:
        await self._run_query('security.sessions.revoke_session', (str(session_guid),))

  async def logout_device(self, token: str) -> None:
    await self._run_query('security.sessions.revoke_token', (self._hash_token(token),))

  async def get_session(
    self,
    token: str,
    ip_address: str | None,
    user_agent: str | None,
  ) -> dict:
    validated = await self._run_query('security.sessions.validate_token', (self._hash_token(token),))
    row = validated.rows[0] if validated and validated.rows else None
    if not row:
      raise HTTPException(status_code=401, detail='Invalid session token')
    if str(row.get('token_type') or '').lower() != 'access':
      raise HTTPException(status_code=401, detail='Invalid token type')

    session_guid = str(row.get('session_guid'))
    session = await self._run_query('security.sessions.get_session', (session_guid,))
    payload = session.rows[0] if session and session.rows else None
    if not payload:
      raise HTTPException(status_code=401, detail='Invalid session token')

    expires_at = self._as_utc(payload.get('expires_at'))
    if expires_at and expires_at < datetime.now(timezone.utc):
      raise HTTPException(status_code=401, detail='Session expired')
    if payload.get('revoked_at') or not payload.get('is_active', True):
      raise HTTPException(status_code=401, detail='Session revoked')

    await self._run_query('security.sessions.update_device', (ip_address, user_agent, session_guid))

    return {
      'session_guid': payload.get('session_guid'),
      'user_guid': payload.get('user_guid'),
      'issued_at': None,
      'expires_at': payload.get('expires_at'),
      'device_fingerprint': payload.get('device_fingerprint'),
      'user_agent': payload.get('user_agent'),
      'ip_last_seen': payload.get('ip_address'),
      'device_guid': None,
    }

  async def get_user_context(self, user_guid: str, session_guid: str, session_type: str) -> dict:
    context = await self._run_query('security.sessions.get_user_context', (user_guid,))
    row = context.rows[0] if context and context.rows else {}

    return {
      'display': row.get('display') or '',
      'email': row.get('email') or '',
      'roles': self._extract_name_list(row.get('roles')),
      'entitlements': self._extract_name_list(row.get('entitlements')),
      'providers': self._extract_name_list(row.get('providers')),
      'sessionType': session_type or 'browser',
      'isAuthenticated': bool(user_guid and session_guid),
    }

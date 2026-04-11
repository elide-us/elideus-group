from __future__ import annotations

import base64
import contextvars
import hashlib
import hmac
import json
import logging
import secrets
from collections import deque
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from os import getenv
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from jose import jwt
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import ToolAnnotations
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule
from .oauth_module import OauthModule
from .role_module import RoleModule

_AUTH_CONTEXT: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar('mcp_auth', default=None)
_TOOL_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


class SlidingWindowRateLimiter:
  def __init__(self, window_seconds: float):
    self._window = window_seconds
    self._counters: dict[str, deque[float]] = {}
    self._global: deque[float] = deque()

  def check(self, key: str, per_key_limit: int, global_limit: int) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - self._window
    while self._global and self._global[0] < cutoff:
      self._global.popleft()
    if len(self._global) >= global_limit:
      return False
    counter = self._counters.get(key)
    if counter is None:
      counter = deque()
      self._counters[key] = counter
    while counter and counter[0] < cutoff:
      counter.popleft()
    if len(counter) >= per_key_limit:
      return False
    counter.append(now)
    self._global.append(now)
    return True


class McpIoServiceModule(BaseModule):
  MODULE_GUID = '3898D988-258E-5529-8218-8F053886D48E'
  SESSION_TYPE_AGENT = '503A571B-2FAB-5828-AA12-E05FF018D4B7'
  TOKEN_TYPE_ACCESS = '8AA0F073-7CA1-5375-9989-67DB2688BDF5'
  TOKEN_TYPE_REFRESH = '8E312303-3EA8-5D6F-9341-D201D5A9ABA6'

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.auth: AuthModule | None = None
    self.role: RoleModule | None = None
    self.oauth: OauthModule | None = None
    self.gateway_guid: str = ''
    self.hostname: str = ''
    self.strategies: list[dict[str, Any]] = []
    self.bindings: dict[str, dict[str, Any]] = {}
    self._queries: dict[str, str] = {}
    self.mcp: FastMCP | None = None
    self.session_manager: StreamableHTTPSessionManager | None = None
    self.register_rate_limiter = SlidingWindowRateLimiter(window_seconds=60.0)
    self.token_rate_limiter = SlidingWindowRateLimiter(window_seconds=60.0)
    self._AUTH_CONTEXT = _AUTH_CONTEXT

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.auth = self.app.state.auth
    await self.auth.on_ready()
    self.role = self.app.state.role
    await self.role.on_ready()
    self.oauth = self.app.state.oauth
    await self.oauth.on_ready()
    await self._load_queries()
    await self.refresh_runtime_config()
    await self._load_gateway_data()
    self._build_mcp()
    self.session_manager = StreamableHTTPSessionManager(app=self.mcp._mcp_server, json_response=True, stateless=True)
    self.mark_ready()

  async def shutdown(self):
    self.session_manager = None
    self.mcp = None

  async def _load_queries(self):
    sql = """
SELECT pub_name, pub_query_text
FROM system_objects_queries
WHERE ref_module_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
  AND pub_is_active = 1
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""
    loaded = await run_json_many(sql, (self.MODULE_GUID,))
    rows = loaded.rows if loaded else []
    self._queries = {
      str(row.get('pub_name')): str(row.get('pub_query_text'))
      for row in rows
      if row.get('pub_name') and row.get('pub_query_text')
    }

  async def _run_query(self, query_name: str, params: tuple = ()) -> Any:
    sql = self._queries.get(query_name)
    if not sql:
      raise RuntimeError(f'Query not loaded: {query_name}')
    if 'FOR JSON' in sql:
      if 'WITHOUT_ARRAY_WRAPPER' in sql:
        return await run_json_one(sql, params)
      return await run_json_many(sql, params)
    return await run_exec(sql, params)

  async def _load_gateway_data(self):
    assert self.db
    gateway_sql = """
SELECT key_guid, pub_name, ref_transport_guid, pub_description, ref_module_guid, pub_is_active
FROM system_objects_io_gateways
WHERE pub_name = ?
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
"""
    gateway_result = await run_json_one(gateway_sql, ('mcp',))
    gateway_row = self._coerce_row(gateway_result.rows if gateway_result else None)
    if not gateway_row:
      raise RuntimeError('MCP gateway registration was not found')
    self.gateway_guid = str(gateway_row.get('key_guid') or '')
    self.hostname = getenv('HOSTNAME', 'localhost')

    strategy_sql = """
SELECT ip.key_guid, ip.ref_strategy_guid, ip.pub_priority, ip.pub_description, v.pub_name AS strategy_name
FROM system_objects_gateway_identity_providers ip
JOIN service_enum_values v ON v.key_guid = ip.ref_strategy_guid
WHERE ip.ref_gateway_guid = ?
  AND ip.pub_is_active = 1
ORDER BY ip.pub_priority
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""
    strategies_result = await run_json_many(strategy_sql, (self.gateway_guid,))
    self.strategies = [self._coerce_dict(row) for row in (strategies_result.rows if strategies_result else [])]

    binding_sql = """
SELECT mb.key_guid, mb.pub_operation_name, mb.pub_required_scope,
       mb.ref_required_role_guid, mb.ref_required_entitlement_guid,
       mm.pub_name AS method_name, mod.pub_state_attr AS module_attr
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
JOIN system_objects_modules mod ON mod.key_guid = mm.ref_module_guid
WHERE mb.ref_gateway_guid = ?
  AND mb.pub_is_active = 1
ORDER BY mb.pub_operation_name
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""
    bindings_result = await run_json_many(binding_sql, (self.gateway_guid,))
    self.bindings = {}
    for row in (bindings_result.rows if bindings_result else []):
      data = self._coerce_dict(row)
      op = str(data.get('pub_operation_name') or '')
      if op:
        self.bindings[op] = data

  def _build_mcp(self):
    self.mcp = FastMCP('oracle_rpc_mcp')

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_tables(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_tables', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_describe_table(ctx: Context, table_name: str, table_schema: str = 'dbo') -> Any:
      return await self.dispatch('oracle_describe_table', ctx, table_name=table_name, table_schema=table_schema)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_views(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_views', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_get_full_schema(ctx: Context) -> Any:
      return await self.dispatch('oracle_get_full_schema', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_get_schema_version(ctx: Context) -> Any:
      return await self.dispatch('oracle_get_schema_version', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_dump_table(ctx: Context, table_name: str, table_schema: str = 'dbo', max_rows: int = 100) -> Any:
      return await self.dispatch('oracle_dump_table', ctx, table_name=table_name, table_schema=table_schema, max_rows=max_rows)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_query_info_schema(ctx: Context, view_name: str, filter_column: str | None = None, filter_value: str | None = None) -> Any:
      return await self.dispatch('oracle_query_info_schema', ctx, view_name=view_name, filter_column=filter_column, filter_value=filter_value)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_domains(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_domains', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_endpoints(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_endpoints', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_domains(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_domains', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_subdomains(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_subdomains', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_functions(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_functions', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_models(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_models', ctx)

    @self.mcp.tool(annotations=_TOOL_ANNOTATIONS)
    async def oracle_list_rpc_model_fields(ctx: Context) -> Any:
      return await self.dispatch('oracle_list_rpc_model_fields', ctx)

  async def dispatch(self, operation_name: str, ctx: Context, **kwargs: Any) -> Any:
    binding = self.bindings.get(operation_name)
    if not binding:
      raise HTTPException(status_code=404, detail='Unknown MCP operation')

    auth_data = _AUTH_CONTEXT.get()
    if auth_data is None:
      request_context = getattr(ctx, 'request_context', None)
      request = getattr(request_context, 'request', None) if request_context else None
      if request is not None:
        auth_data = getattr(request.state, 'mcp_auth', None)
    bearer = str(auth_data.get('token') or '') if auth_data else None

    identity = await self.resolve_identity(bearer)
    if identity is None:
      raise HTTPException(status_code=401, detail='Not authenticated')
    if not await self.check_authorization(identity, binding):
      raise HTTPException(status_code=403, detail='Forbidden')

    module_attr = str(binding.get('module_attr') or '')
    method_name = str(binding.get('method_name') or '')
    module = getattr(self.app.state, module_attr, None)
    if module is None or not method_name:
      raise HTTPException(status_code=500, detail='MCP binding misconfigured')
    await module.on_ready()
    method = getattr(module, method_name, None)
    if method is None:
      raise HTTPException(status_code=500, detail='MCP method missing')
    return await method(**kwargs)

  async def resolve_identity(self, bearer_token: str | None) -> dict[str, Any] | None:
    assert self.auth
    assert self.role

    for strategy in self.strategies:
      strategy_name = str(strategy.get('strategy_name') or '')

      if strategy_name == 'static_token' and bearer_token:
        static_token = getenv('MCP_AGENT_TOKEN', '')
        if static_token and bearer_token == static_token:
          return {
            'user_guid': None,
            'roles': [],
            'entitlements': [],
            'scopes': {
              'mcp:schema:read', 'mcp:data:read', 'mcp:rpc:list', 'mcp:schema:write',
              'mcp:data:write', 'mcp:rpc:execute', 'mcp:admin',
            },
            'source': 'static_token',
          }

      if strategy_name == 'bearer_jwt' and bearer_token:
        try:
          claims = await self.auth.decode_session_token(bearer_token)
          user_guid = str(claims.get('sub') or '')
          if not user_guid:
            continue
          roles, _ = await self.role.get_user_roles(user_guid)
          return {
            'user_guid': user_guid,
            'roles': roles,
            'entitlements': [],
            'scopes': set(claims.get('scopes') or []),
            'source': 'bearer_jwt',
          }
        except Exception:
          if not self.auth.jwt_secret:
            continue
          try:
            claims = jwt.decode(bearer_token, self.auth.jwt_secret, algorithms=[self.auth.jwt_algo_int])
            if claims.get('type') != 'mcp_access':
              continue
            user_guid = str(claims.get('sub') or '')
            if not user_guid:
              continue
            roles, _ = await self.role.get_user_roles(user_guid)
            scopes = claims.get('scopes') or []
            if isinstance(scopes, str):
              scopes = scopes.split()
            return {
              'user_guid': user_guid,
              'roles': roles,
              'entitlements': [],
              'scopes': set(scopes),
              'source': 'bearer_jwt',
            }
          except Exception:
            logging.debug('[McpIoServiceModule] bearer_jwt strategy failed', exc_info=True)

    return None

  async def check_authorization(self, identity: dict[str, Any], binding: dict[str, Any]) -> bool:
    required_scope = binding.get('pub_required_scope')
    if required_scope and str(required_scope) not in set(identity.get('scopes') or []):
      return False

    required_role = binding.get('ref_required_role_guid')
    if required_role:
      roles = {str(role).upper() for role in (identity.get('roles') or [])}
      if str(required_role).upper() not in roles:
        return False

    required_entitlement = binding.get('ref_required_entitlement_guid')
    if required_entitlement:
      entitlements = {str(entitlement).upper() for entitlement in (identity.get('entitlements') or [])}
      if str(required_entitlement).upper() not in entitlements:
        return False

    return True

  async def is_dcr_enabled(self) -> bool:
    return False

  async def check_register_rate(self, ip: str) -> bool:
    return self.register_rate_limiter.check(ip, 5, 50)

  async def check_token_rate(self, ip: str) -> bool:
    return self.token_rate_limiter.check(ip, 60, 500)


  async def register_client(
    self,
    client_name: str,
    redirect_uris: Any,
    grant_types: Any,
    response_types: Any,
    scopes: str,
    ip_address: str | None,
    user_agent: str | None,
  ) -> dict:
    raise HTTPException(status_code=503, detail='Dynamic client registration is disabled')
  async def get_client(self, client_id: str) -> dict | None:
    result = await self._run_query('security.agents.get_client_by_id', (client_id,))
    return result.rows[0] if result and result.rows else None

  async def link_client_to_user(self, client_id: str, users_guid: str) -> None:
    await self._run_query('security.agents.link_client_user', (client_id, users_guid))

  async def create_authorization_code(self, agents_recid: int, users_guid: str, code_challenge: str, code_method: str, redirect_uri: str, scopes: str) -> str:
    code = secrets.token_urlsafe(32)
    expires_on = datetime.now(timezone.utc) + timedelta(seconds=60)
    await self._run_query('security.agents.create_auth_code', (agents_recid, users_guid, code, code_challenge, code_method, redirect_uri, scopes, expires_on))
    return code

  async def exchange_authorization_code(self, code: str, code_verifier: str, client_id: str) -> dict:
    consumed = await self._run_query('security.agents.consume_auth_code', (code,))
    row = consumed.rows[0] if consumed and consumed.rows else None
    if not row:
      raise HTTPException(status_code=400, detail='Invalid or expired authorization code')

    expected = str(row.get('element_code_challenge') or '')
    digest = hashlib.sha256(str(code_verifier).encode('utf-8')).digest()
    verifier_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    if verifier_challenge != expected:
      raise HTTPException(status_code=400, detail='PKCE verification failed')

    client = await self.get_client(client_id)
    if not client or int(client.get('recid') or 0) != int(row.get('agents_recid') or 0):
      raise HTTPException(status_code=400, detail='Client does not match authorization code')

    tokens = await self._issue_agent_tokens(str(row.get('users_guid') or ''), client_id, str(row.get('element_scopes') or ''))
    return tokens

  async def refresh_access_token(self, refresh_token: str) -> dict:
    validated = await self._run_query('security.sessions.validate_token', (self._hash_token(refresh_token),))
    row = validated.rows[0] if validated and validated.rows else None
    if not row or str(row.get('token_type') or '').lower() != 'refresh':
      raise HTTPException(status_code=401, detail='Invalid refresh token')
    user_guid = str(row.get('user_guid') or '')
    tokens = await self._issue_agent_tokens(user_guid, str(row.get('client_id') or ''), 'mcp:schema:read mcp:data:read mcp:rpc:list', refresh_token=refresh_token, session_guid=str(row.get('session_guid') or ''))
    return tokens

  async def check_user_mcp_role(self, user_guid: str) -> bool:
    assert self.auth
    return await self.auth.user_has_role(user_guid, 32)

  async def refresh_runtime_config(self):
    self.hostname = await self._get_config_value('Hostname', fallback='localhost')

  async def _get_config_value(self, key: str, *, fallback: str = '') -> str:
    result = await run_json_many('SELECT element_value FROM system_config WHERE element_key = ? FOR JSON PATH, INCLUDE_NULL_VALUES;', (key,))
    rows = result.rows if result else []
    if not rows:
      return fallback
    value = rows[0].get('element_value')
    return str(value) if value is not None else fallback

  async def _issue_agent_tokens(self, user_guid: str, client_id: str, scopes: str, refresh_token: str | None = None, session_guid: str | None = None) -> dict:
    assert self.auth
    assert self.role
    if not user_guid:
      raise HTTPException(status_code=401, detail='Authorization code is not linked to a user')
    now = datetime.now(timezone.utc)
    access_exp = now + timedelta(minutes=5)
    refresh_exp = now + timedelta(days=7)
    roles, _ = await self.role.get_user_roles(user_guid)
    claims = {
      'sub': user_guid,
      'client_id': client_id,
      'scopes': scopes,
      'roles': roles,
      'iss': self.hostname,
      'iat': int(now.timestamp()),
      'exp': int(access_exp.timestamp()),
      'jti': uuid4().hex,
      'type': 'mcp_access',
    }
    access_token = jwt.encode(claims, self.auth.jwt_secret, algorithm=self.auth.jwt_algo_int)
    refresh_token = refresh_token or secrets.token_urlsafe(48)

    if not session_guid:
      created = await self._run_query('security.sessions.create_session', (
        user_guid,
        self.SESSION_TYPE_AGENT,
        access_exp,
        self._hash_token(access_token),
        scopes,
        access_exp,
        self._hash_token(refresh_token),
        scopes,
        refresh_exp,
        self._hash_token(secrets.token_urlsafe(32)),
        refresh_exp,
        f'mcp:{client_id}',
        'mcp-oauth',
        None,
      ))
      row = created.rows[0] if created and created.rows else None
      if not row:
        raise HTTPException(status_code=500, detail='Failed to create session')
      session_guid = str(row.get('session_guid') or '')
    await self._run_query('security.sessions.create_token', (session_guid, self.TOKEN_TYPE_ACCESS, self._hash_token(access_token), scopes, access_exp))
    await self._run_query('security.sessions.create_token', (session_guid, self.TOKEN_TYPE_REFRESH, self._hash_token(refresh_token), scopes, refresh_exp))

    return {
      'access_token': access_token,
      'refresh_token': refresh_token,
      'token_type': 'Bearer',
      'expires_in': 300,
      'scope': scopes,
    }

  def _hash_token(self, token: str) -> str:
    assert self.auth
    key = self.auth.jwt_secret.encode('utf-8')
    return hmac.new(key, token.encode('utf-8'), hashlib.sha256).hexdigest()

  @staticmethod
  def _coerce_row(rows: Any) -> dict[str, Any] | None:
    if not rows:
      return None
    if isinstance(rows, Mapping):
      return dict(rows)
    if isinstance(rows, list) and rows and isinstance(rows[0], Mapping):
      return dict(rows[0])
    return None

  @staticmethod
  def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
      return dict(value)
    return {}

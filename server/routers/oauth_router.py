###  """OAuth endpoints for MCP dynamic client registration and authorization flows."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import jwt

from server.modules.providers.auth.discord_provider import AUTHORIZE_URL as DISCORD_AUTHORIZE_URL

router = APIRouter()

_SCOPE_DESCRIPTIONS = {
  "mcp:schema:read": "Read schema metadata (tables, views, column information).",
  "mcp:data:read": "Read reflected data and information schema payloads.",
  "mcp:rpc:list": "List available RPC domains and endpoints.",
}

_PROVIDER_LABELS = {
  "microsoft": "Microsoft",
  "google": "Google",
  "discord": "Discord",
}

_PROVIDER_AUTHORIZE_URLS = {
  "microsoft": "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize",
  "google": "https://accounts.google.com/o/oauth2/v2/auth",
  "discord": DISCORD_AUTHORIZE_URL,
}

_PROVIDER_SCOPES = {
  "microsoft": "openid profile email User.Read",
  "google": "openid email profile",
  "discord": "identify email",
}

_PROVIDER_SECRET_VARS = {
  "microsoft": "MICROSOFT_AUTH_SECRET",
  "google": "GOOGLE_AUTH_SECRET",
  "discord": "DISCORD_AUTH_SECRET",
}


@router.get("/.well-known/oauth-protected-resource")
async def get_protected_resource_metadata(request: Request):
  hostname = request.app.state.mcp_io_service.hostname
  return {
    "resource": f"https://{hostname}/mcp",
    "authorization_servers": [f"https://{hostname}"],
    "scopes_supported": [
      "mcp:schema:read",
      "mcp:data:read",
      "mcp:rpc:list",
    ],
    "bearer_methods_supported": ["header"],
  }


@router.get("/.well-known/oauth-authorization-server")
async def get_authorization_server_metadata(request: Request):
  hostname = request.app.state.mcp_io_service.hostname
  return {
    "issuer": f"https://{hostname}",
    "authorization_endpoint": f"https://{hostname}/oauth/authorize",
    "token_endpoint": f"https://{hostname}/oauth/token",
    "registration_endpoint": f"https://{hostname}/oauth/register",
    "scopes_supported": [
      "mcp:schema:read",
      "mcp:data:read",
      "mcp:rpc:list",
    ],
    "response_types_supported": ["code"],
    "grant_types_supported": ["authorization_code", "refresh_token"],
    "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
    "code_challenge_methods_supported": ["S256"],
    "service_documentation": f"https://{hostname}/docs/mcp",
  }


@router.post("/oauth/register")
async def post_oauth_register(request: Request):
  gateway = request.app.state.mcp_io_service

  if not await gateway.is_dcr_enabled():
    raise HTTPException(status_code=403, detail="Dynamic client registration is disabled")

  ip = request.client.host if request.client else "unknown"
  if not await gateway.check_register_rate(ip):
    raise HTTPException(status_code=429, detail="Rate limit exceeded")

  body = await request.json()
  client_name = body.get("client_name")
  if not client_name:
    raise HTTPException(status_code=400, detail="client_name is required")

  result = await gateway.register_client(
    client_name=client_name,
    redirect_uris=body.get("redirect_uris"),
    grant_types=body.get("grant_types", "authorization_code"),
    response_types=body.get("response_types", "code"),
    scopes=body.get("scope", "mcp:schema:read mcp:data:read mcp:rpc:list"),
    ip_address=ip,
    user_agent=request.headers.get("user-agent"),
  )
  return JSONResponse(status_code=201, content=result)


def _get_signing_secret(request: Request) -> str:
  secret = getattr(request.app.state.auth, "jwt_secret", None)
  if not secret:
    raise HTTPException(status_code=500, detail="OAuth signing key is not configured")
  return secret


def _parse_redirect_uris(raw_value: Any) -> set[str]:
  if not raw_value:
    return set()
  if isinstance(raw_value, list):
    return {str(item) for item in raw_value if str(item).strip()}
  raw = str(raw_value).strip()
  if not raw:
    return set()
  try:
    parsed = json.loads(raw)
    if isinstance(parsed, list):
      return {str(item) for item in parsed if str(item).strip()}
  except json.JSONDecodeError:
    pass
  if "," in raw:
    return {item.strip() for item in raw.split(",") if item.strip()}
  if " " in raw:
    return {item.strip() for item in raw.split(" ") if item.strip()}
  return {raw}


def _sign_flow_state(request: Request, payload: dict[str, Any]) -> str:
  secret = _get_signing_secret(request)
  exp = datetime.now(timezone.utc) + timedelta(minutes=10)
  return jwt.encode({**payload, "exp": int(exp.timestamp())}, secret, algorithm="HS256")


def _decode_flow_state(request: Request, token: str) -> dict[str, Any]:
  secret = _get_signing_secret(request)
  try:
    return jwt.decode(token, secret, algorithms=["HS256"])
  except Exception as exc:
    raise HTTPException(status_code=400, detail="Invalid authorization state") from exc


def _provider_client_id(gateway: Any, provider: str) -> str:
  provider_obj = gateway.oauth.auth.providers.get(provider)
  audience = getattr(provider_obj, "audience", None) if provider_obj else None
  if not audience:
    raise HTTPException(status_code=500, detail=f"{provider.title()} OAuth is not configured")
  return str(audience)


def _provider_secret(gateway: Any, provider: str) -> str:
  secret_var = _PROVIDER_SECRET_VARS.get(provider)
  env_module = getattr(gateway.oauth, "env", None)
  if not secret_var or not env_module:
    raise HTTPException(status_code=500, detail=f"{provider.title()} OAuth is not configured")
  secret = env_module.get(secret_var)
  if not secret:
    raise HTTPException(status_code=500, detail=f"{provider.title()} OAuth is not configured")
  return secret


def _callback_uri(hostname: str, provider: str) -> str:
  return f"https://{hostname}/oauth/callback/{provider}"


def _render_authorize_page(client_name: str, requested_scopes: list[str], provider_links: dict[str, str]) -> str:
  scope_items = "".join(
    f"<li><code>{scope}</code> — {_SCOPE_DESCRIPTIONS.get(scope, 'Requested access')}</li>"
    for scope in requested_scopes
  )
  provider_buttons = "".join(
    (
      f"<a class='btn' href='{provider_links[provider]}'>{_PROVIDER_LABELS[provider]}</a>"
      for provider in ("microsoft", "google", "discord")
    )
  )
  return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>MCP OAuth Consent</title>
    <style>
      body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
      .card {{ max-width: 720px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 1.5rem; }}
      h1 {{ margin-top: 0; color: #f8fafc; }}
      ul {{ line-height: 1.6; }}
      code {{ color: #93c5fd; }}
      .buttons {{ display: flex; gap: 0.75rem; margin-top: 1.5rem; flex-wrap: wrap; }}
      .btn {{ background: #2563eb; color: white; text-decoration: none; padding: 0.75rem 1rem; border-radius: 8px; font-weight: 600; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>{client_name} wants to access Oracle RPC</h1>
      <p>Requested permissions:</p>
      <ul>{scope_items}</ul>
      <p>Continue with a login provider:</p>
      <div class=\"buttons\">{provider_buttons}</div>
    </div>
  </body>
</html>
"""


# ── /oauth/authorize ─────────────────────────────────────────────────────
# Client lookup returns new-table column names:
#   client_guid, client_id, client_name, redirect_uris,
#   grant_types, response_types, scopes, is_dcr, is_active, revoked_at

@router.get("/oauth/authorize", response_class=HTMLResponse)
async def get_oauth_authorize(
  request: Request,
  client_id: str,
  redirect_uri: str,
  response_type: str,
  scope: str = "mcp:schema:read mcp:data:read mcp:rpc:list",
  state: str | None = None,
  code_challenge: str | None = None,
  code_challenge_method: str | None = None,
):
  gateway = request.app.state.mcp_io_service
  client = await gateway.get_client(client_id)
  if not client or not client.get("is_active"):
    raise HTTPException(status_code=400, detail="Unknown or inactive client")

  registered_uris = _parse_redirect_uris(client.get("redirect_uris"))
  if redirect_uri not in registered_uris:
    raise HTTPException(status_code=400, detail="redirect_uri is not registered for this client")

  if response_type != "code":
    raise HTTPException(status_code=400, detail="Unsupported response_type")
  if code_challenge_method != "S256" or not code_challenge:
    raise HTTPException(status_code=400, detail="PKCE S256 code_challenge is required")

  requested_scopes = [segment for segment in scope.split() if segment]
  flow_state = _sign_flow_state(
    request,
    {
      "client_id": client_id,
      "redirect_uri": redirect_uri,
      "state": state,
      "scope": " ".join(requested_scopes),
      "code_challenge": code_challenge,
      "code_challenge_method": code_challenge_method,
    },
  )

  provider_links: dict[str, str] = {}
  for provider in ("microsoft", "google", "discord"):
    login_params = urlencode({"provider": provider, "flow": flow_state})
    provider_links[provider] = f"/oauth/provider-login?{login_params}"

  return HTMLResponse(_render_authorize_page(
    str(client.get("client_name") or "Client"),
    requested_scopes,
    provider_links,
  ))


@router.get("/oauth/provider-login")
async def get_oauth_provider_login(request: Request, provider: str, flow: str):
  provider = provider.lower()
  if provider not in _PROVIDER_AUTHORIZE_URLS:
    raise HTTPException(status_code=400, detail="Unsupported provider")

  flow_payload = _decode_flow_state(request, flow)
  hostname = request.app.state.mcp_io_service.hostname
  callback = _callback_uri(hostname, provider)
  provider_code_verifier = secrets.token_urlsafe(32)
  provider_code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(provider_code_verifier.encode("utf-8")).digest()
  ).decode("utf-8").rstrip("=")
  state_payload = _sign_flow_state(
    request,
    {
      "provider": provider,
      "flow": flow_payload,
      "nonce": base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("="),
      "provider_code_verifier": provider_code_verifier,
    },
  )

  params = {
    "response_type": "code",
    "client_id": _provider_client_id(request.app.state.mcp_io_service, provider),
    "redirect_uri": callback,
    "scope": _PROVIDER_SCOPES[provider],
    "state": state_payload,
    "code_challenge": provider_code_challenge,
    "code_challenge_method": "S256",
  }
  if provider == "google":
    params["access_type"] = "offline"
    params["prompt"] = "consent"

  return RedirectResponse(f"{_PROVIDER_AUTHORIZE_URLS[provider]}?{urlencode(params)}", status_code=302)


# ── /oauth/callback/{provider} ───────────────────────────────────────────
# After identity provider login completes, we:
#   1. Exchange provider code for tokens
#   2. Resolve/create user via OauthModule
#   3. Look up the MCP client by pub_client_id
#   4. Link client to user (using internal client_guid)
#   5. Create an authorization code
#   6. Redirect back to the MCP client's redirect_uri

@router.get("/oauth/callback/{provider}")
async def get_oauth_provider_callback(
  request: Request,
  provider: str,
  code: str | None = None,
  state: str | None = None,
  error: str | None = None,
  error_description: str | None = None,
):
  provider = provider.lower()
  if error:
    detail = error_description or error
    raise HTTPException(status_code=400, detail=f"Provider authentication failed: {detail}")
  if not state or not code:
    raise HTTPException(status_code=400, detail="Missing code or state")
  callback_state = _decode_flow_state(request, state)
  if callback_state.get("provider") != provider:
    raise HTTPException(status_code=400, detail="Provider state mismatch")
  logging.info("[MCP OAuth] Provider callback received: provider=%s", provider)

  flow = callback_state.get("flow")
  if not isinstance(flow, dict):
    raise HTTPException(status_code=400, detail="Authorization flow is invalid")

  gateway = request.app.state.mcp_io_service
  hostname = gateway.hostname
  redirect_uri = _callback_uri(hostname, provider)
  provider_code_verifier = callback_state.get("provider_code_verifier")
  id_token, access_token = await gateway.oauth.exchange_code_for_tokens(
    code=code,
    client_id=_provider_client_id(gateway, provider),
    client_secret=_provider_secret(gateway, provider),
    redirect_uri=redirect_uri,
    provider=provider,
    code_verifier=provider_code_verifier,
  )
  logging.info(
    "[MCP OAuth] Provider %s token exchange complete for flow client_id=%s",
    provider,
    flow.get("client_id"),
  )
  provider_uid, profile, payload = await gateway.auth.handle_auth_login(provider, id_token, access_token)
  logging.info(
    "[MCP OAuth] Authenticated user: %s via %s",
    profile.get("email") or profile.get("username"),
    provider,
  )
  provider_uid = gateway.oauth.normalize_provider_identifier(provider_uid)
  user = await gateway.oauth.resolve_user(provider, provider_uid, profile, payload)
  logging.info("[MCP OAuth] Resolved user guid=%s", user.get("guid"))
  user_guid = str(user.get("guid") or "")
  if not user_guid or not await gateway.check_user_mcp_role(user_guid):
    raise HTTPException(status_code=403, detail="User is not authorized for MCP access")

  # Look up the MCP client by the external pub_client_id from the flow state
  client_id = str(flow.get("client_id") or "")
  client = await gateway.get_client(client_id)
  if not client:
    raise HTTPException(status_code=400, detail="Unknown OAuth client")

  # Internal client_guid for FK references (NOT the external pub_client_id)
  client_guid = str(client.get("client_guid") or "")
  client_name = str(client.get("client_name") or "Client")

  logging.info(
    "[MCP OAuth] Resolved user_guid=%s for client '%s'",
    user_guid, client_name,
  )
  if not user_guid:
    raise HTTPException(status_code=400, detail="User account record is missing")

  # Link using internal GUIDs
  await gateway.link_client_to_user(client_guid, user_guid)
  auth_code = await gateway.create_authorization_code(
    client_guid=client_guid,
    user_guid=user_guid,
    code_challenge=str(flow.get("code_challenge") or ""),
    code_method=str(flow.get("code_challenge_method") or "S256"),
    redirect_uri=str(flow.get("redirect_uri") or ""),
    scopes=str(flow.get("scope") or ""),
  )

  final_redirect_uri = str(flow.get("redirect_uri") or "")
  final_state = flow.get("state")
  params = {"code": auth_code}
  if final_state is not None:
    params["state"] = final_state

  logging.info(
    "[MCP OAuth] Authorization code issued for client '%s', redirecting to %s",
    client_name, final_redirect_uri,
  )

  return RedirectResponse(f"{final_redirect_uri}?{urlencode(params)}", status_code=302)


@router.post("/oauth/token")
async def post_oauth_token(request: Request):
  gateway = request.app.state.mcp_io_service

  ip = request.client.host if request.client else "unknown"
  if not await gateway.check_token_rate(ip):
    raise HTTPException(status_code=429, detail="Rate limit exceeded")

  content_type = request.headers.get("content-type", "")
  if "application/x-www-form-urlencoded" in content_type:
    form = await request.form()
    body = dict(form)
  else:
    body = await request.json()

  grant_type = body.get("grant_type")

  if grant_type == "authorization_code":
    result = await gateway.exchange_authorization_code(
      code=body.get("code"),
      code_verifier=body.get("code_verifier"),
      client_id=body.get("client_id"),
    )
    return result

  if grant_type == "refresh_token":
    result = await gateway.refresh_access_token(
      refresh_token=body.get("refresh_token"),
    )
    return result

  raise HTTPException(status_code=400, detail="Unsupported grant_type")
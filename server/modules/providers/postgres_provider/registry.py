# providers/postgres_provider/registry.py
from typing import Any, Awaitable, Callable, Dict, Tuple
from uuid import UUID
from .logic import execute, fetch_one, fetch_many, transaction

_REG: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

def register(op: str):
  def deco(fn):
    if op in _REG:
      raise ValueError(f"Duplicate op: {op}")
    _REG[op] = fn
    return fn
  return deco

def get_handler(op: str):
  try:
    return _REG[op]
  except KeyError:
    raise KeyError(f"No PostgreSQL handler for '{op}'")

@register("urn:users:providers:get_by_provider_identifier:1")
def _users_select(args: Dict[str, Any]):
  provider = args["provider"]
  identifier = str(UUID(args["provider_identifier"]))
  sql = """
    SELECT
      v.user_guid AS guid,
      v.display_name AS display_name,
      v.email AS email,
      v.credits,
      v.provider_name,
      v.provider_display,
      v.profile_image_base64 AS profile_image
    FROM vw_account_user_profile v
    JOIN users_auth ua ON ua.users_guid = v.user_guid
    JOIN auth_providers ap ON ap.recid = ua.providers_recid
    WHERE ap.element_name = $1 AND ua.element_identifier = $2
    LIMIT 1;
  """
  return ("one", sql, (provider, identifier))

@register("urn:users:profile:get_roles:1")
def _users_get_roles(args: Dict[str, Any]):
  guid = args["guid"]
  sql = """
    SELECT element_roles FROM users_roles
    WHERE users_guid = $1;
  """
  return ("many", sql, (guid,))

@register("urn:users:profile:set_roles:1")
async def _users_set_roles(args: Dict[str, Any]):
  guid, roles = args["guid"], int(args["roles"])
  rc = await execute(
    "UPDATE users_roles SET element_roles = $1 WHERE users_guid = $2;",
    (roles, guid)
  )
  if rc == 0:
    rc = await execute(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES ($1, $2);",
      (guid, roles)
    )
  return {"rows": [], "rowcount": rc}

@register("db:users:session:set_rotkey:1")
def _users_session_set_rotkey(args: Dict[str, Any]):
  guid = args["guid"]
  rotkey = args["rotkey"]
  iat = args["iat"]
  exp = args["exp"]
  sql = """
    UPDATE account_users
    SET element_rotkey = $1, element_rotkey_iat = $2, element_rotkey_exp = $3
    WHERE element_guid = $4;
  """
  return ("exec", sql, (rotkey, iat, exp, guid))

@register("db:users:session:get_rotkey:1")
def _users_session_get_rotkey(args: Dict[str, Any]):
  guid = args["guid"]
  sql = """
    SELECT element_rotkey AS rotkey
    FROM vw_account_user_security
    WHERE user_guid = $1
    LIMIT 1;
  """
  return ("one", sql, (guid,))


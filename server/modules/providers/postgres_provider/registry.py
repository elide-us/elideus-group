# providers/postgres_provider/registry.py
from typing import Any, Awaitable, Callable, Dict, Tuple
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

@register("urn:users:core:get_by_provider_identifier:v1")
def _users_select(args: Dict[str, Any]):
  provider = args["provider"]
  identifier = args["provider_identifier"]
  sql = """
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
    WHERE ap.element_name = $1 AND ua.element_identifier = $2;
  """
  return ("one", sql, (provider, identifier))

@register("urn:users:core:get_roles:v1")
def _users_get_roles(args: Dict[str, Any]):
  guid = args["guid"]
  sql = """
    SELECT element_roles FROM users_roles
    WHERE users_guid = $1;
  """
  return ("many", sql, (guid,))

@register("urn:users:core:set_roles:v1")
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


# providers/mssql_provider/registry.py
from typing import Any, Awaitable, Callable, Dict, Tuple
from .logic import init_pool, close_pool, fetch_json_one, fetch_json_many, exec_, transaction

# handler can be:
#  - sync: (mode, sql, params) -> provider will run it
#  - async: does its own calls and returns {"rows":[...], "rowcount":N}
_REG: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

def register(op: str):
    def deco(fn):
        if op in _REG: raise ValueError(f"Duplicate op: {op}")
        _REG[op] = fn
        return fn
    return deco

def get_handler(op: str):
    try:
        return _REG[op]
    except KeyError:
        raise KeyError(f"No MSSQL handler for '{op}'")

# -------------------- MAPPINGS (representative set) --------------------

@register("urn:users:core:get_by_provider_identifier:v1")
def _users_select(provider_args: Dict[str, Any]):
    provider = provider_args["provider"]
    identifier = provider_args["provider_identifier"]
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
      WHERE ap.element_name = ? AND ua.element_identifier = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return ("json_one", sql, (provider, identifier))

@register("urn:users:core:create_from_provider:v1")
async def _users_insert(args: Dict[str, Any]):
    # mirrors your insert_user() logic, including provider recid lookup + 3 inserts
    from uuid import uuid4
    new_guid = str(uuid4())
    element_rotkey = ""
    from datetime import datetime, timezone
    element_rotkey_iat = datetime.now(timezone.utc)
    element_rotkey_exp = datetime.now(timezone.utc)
    provider = args["provider"]
    identifier = args["provider_identifier"]
    provider_email = args["provider_email"]
    provider_displayname = args["provider_displayname"]

    row = await fetch_json_one(
        "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
        (provider,)
    )
    if not row:
        raise ValueError(f"Unknown auth provider: {provider}")
    ap_recid = row["recid"]

    async with transaction() as cur:
        await cur.execute(
            """
            INSERT INTO account_users (element_guid, element_email, element_display, providers_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (new_guid, provider_email, provider_displayname, ap_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
        )
        await cur.execute(
            "INSERT INTO users_auth (users_guid, providers_recid, element_identifier) VALUES (?, ?, ?);",
            (new_guid, ap_recid, identifier)
        )
        await cur.execute(
            "INSERT INTO users_credits (users_guid, element_credits) VALUES (?, ?);",
            (new_guid, 50)
        )

    # return same shape as select_user
    out = await fetch_json_one(_users_select({"provider": provider, "provider_identifier": identifier})[1],
                               (_users_select({"provider": provider, "provider_identifier": identifier})[2]))
    return {"rows": [out] if out else [], "rowcount": 1 if out else 0}

@register("urn:users:core:get_profile:v1")
def _users_profile(args: Dict[str, Any]):
    guid = args["guid"]
    sql = """
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
    return ("json_one", sql, (guid,))

@register("urn:users:core:get_roles:v1")
def _users_get_roles(args: Dict[str, Any]):
    guid = args["guid"]
    sql = """
      SELECT element_roles FROM users_roles
      WHERE users_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return ("json_one", sql, (guid,))

@register("urn:users:core:set_roles:v1")
async def _users_set_roles(args: Dict[str, Any]):
    guid, roles = args["guid"], int(args["roles"])
    if roles == 0:
        rc = await exec_("DELETE FROM users_roles WHERE users_guid = ?;", (guid,))
        return {"rows": [], "rowcount": rc}
    rc = await exec_(
        "UPDATE users_roles SET element_roles = ? WHERE users_guid = ?;",
        (roles, guid)
    )
    if rc == 0:
        rc = await exec_("INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);", (guid, roles))
    return {"rows": [], "rowcount": rc}

@register("urn:frontend:routes:get_by_role_mask:v1")
def _routes_get(args: Dict[str, Any]):
    mask = int(args.get("role_mask", 0))
    sql = """
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
    return ("json_many", sql, (mask,))

@register("urn:users:core:set_profile_image:v1")
async def _users_set_img(args: Dict[str, Any]):
    guid, image_b64 = args["guid"], args["image_b64"]
    rc = await exec_("UPDATE users_profileimg SET element_base64 = ? WHERE users_guid = ?;", (image_b64, guid))
    if rc == 0:
        rc = await exec_("INSERT INTO users_profileimg (users_guid, element_base64) VALUES (?, ?);", (guid, image_b64))
    return {"rows": [], "rowcount": rc}

@register("urn:sessions:create:v1")
async def _sessions_create(args: Dict[str, Any]):
    from uuid import uuid4
    session_guid = str(uuid4())
    device_guid = str(uuid4())
    access_token = args["access_token"]
    expires = args["expires"]
    fingerprint = args.get("fingerprint")
    user_agent = args.get("user_agent")
    ip_address = args.get("ip_address")
    user_guid = args["user_guid"]

    async with transaction() as cur:
        await cur.execute("""
          INSERT INTO users_sessions (element_guid, users_guid, element_created_at)
          VALUES (?, ?, SYSDATETIMEOFFSET());
        """, (session_guid, user_guid))
        await cur.execute("""
          INSERT INTO sessions_devices (
            element_guid, sessions_guid, element_token, element_token_iat, element_token_exp,
            element_device_fingerprint, element_user_agent, element_ip_last_seen
          ) VALUES (?, ?, ?, SYSDATETIMEOFFSET(), ?, ?, ?, ?);
        """, (device_guid, session_guid, access_token, expires, fingerprint, user_agent, ip_address))

    return {"rows": [{"session_guid": session_guid, "device_guid": device_guid}], "rowcount": 1}

@register("urn:sessions:get_by_access_token:v1")
def _sessions_get(args: Dict[str, Any]):
    token = args["access_token"]
    sql = """
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
    return ("json_one", sql, (token,))

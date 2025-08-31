# providers/database/mssql_provider/registry.py
from typing import Any, Awaitable, Callable, Dict, Tuple
from uuid import UUID
from .logic import init_pool, close_pool, transaction
from .db_helpers import fetch_rows, fetch_json, exec_query

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

@register("urn:users:providers:get_by_provider_identifier:1")
def _users_select(provider_args: Dict[str, Any]):
    provider = provider_args["provider"]
    identifier = str(UUID(provider_args["provider_identifier"]))
    sql = """
      SELECT TOP 1
        v.user_guid AS guid,
        v.display_name,
        v.email,
        v.credits,
        v.provider_name,
        v.provider_display,
        v.profile_image_base64 AS profile_image
      FROM vw_account_user_profile v
      JOIN users_auth ua ON ua.users_guid = v.user_guid
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      WHERE ap.element_name = ? AND ua.element_identifier = ?;
    """
    return ("row_one", sql, (provider, identifier))

@register("urn:users:providers:create_from_provider:1")
async def _users_insert(args: Dict[str, Any]):
    # mirrors your insert_user() logic, including provider recid lookup + 3 inserts
    from uuid import uuid4
    new_guid = str(uuid4())
    element_rotkey = ""
    from datetime import datetime, timezone
    element_rotkey_iat = datetime.now(timezone.utc)
    element_rotkey_exp = datetime.now(timezone.utc)
    provider = args["provider"]
    identifier = str(UUID(args["provider_identifier"]))
    provider_email = args["provider_email"]
    provider_displayname = args["provider_displayname"]
    provider_profileimg = args.get("provider_profile_image", "")

    res = await fetch_json(
      "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
      (provider,)
    )
    if not res.rows:
      raise ValueError(f"Unknown auth provider: {provider}")
    ap_recid = res.rows[0]["recid"]

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
        await cur.execute(
            "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
            (new_guid, provider_profileimg, ap_recid)
        )
        await cur.execute(
            "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
            (new_guid, 1)
        )

    # return same shape as select_user
    sel = _users_select({"provider": provider, "provider_identifier": identifier})
    return await fetch_rows(sel[1], sel[2], one=True)

@register("urn:users:providers:link_provider:1")
async def _users_link_provider(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    provider = args["provider"]
    identifier = str(UUID(args["provider_identifier"]))
    res = await fetch_json(
      "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
      (provider,)
    )
    if not res.rows:
      raise ValueError(f"Unknown auth provider: {provider}")
    ap_recid = res.rows[0]["recid"]
    rc = await exec_query(
      "INSERT INTO users_auth (users_guid, providers_recid, element_identifier) VALUES (?, ?, ?);",
      (guid, ap_recid, identifier)
    )
    return rc

@register("urn:users:providers:unlink_provider:1")
async def _users_unlink_provider(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    provider = args["provider"]
    new_recid = args.get("new_provider_recid")
    async with transaction() as cur:
      await cur.execute(
        "SELECT providers_recid FROM account_users WHERE element_guid = ?;",
        (guid,)
      )
      row = await cur.fetchone()
      current_recid = row[0] if row else None
      await cur.execute(
        "SELECT recid FROM auth_providers WHERE element_name = ?;",
        (provider,)
      )
      row = await cur.fetchone()
      provider_recid = row[0] if row else None
      await cur.execute(
        """
        DELETE ua FROM users_auth ua
        JOIN auth_providers ap ON ap.recid = ua.providers_recid
        WHERE ua.users_guid = ? AND ap.element_name = ?;
        """,
        (guid, provider)
      )
      await cur.execute(
        "SELECT COUNT(*) AS cnt FROM users_auth WHERE users_guid = ?;",
        (guid,)
      )
      row = await cur.fetchone()
      cnt = row[0] if row else 0
      if cnt == 0:
        await cur.execute(
          "UPDATE users_roles SET element_roles = 0 WHERE users_guid = ?;",
          (guid,)
        )
        await cur.execute(
          "UPDATE account_users SET providers_recid = NULL WHERE element_guid = ?;",
          (guid,)
        )
      elif current_recid == provider_recid:
        if new_recid is not None:
          await cur.execute(
            "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
            (new_recid, guid),
          )
        else:
          await cur.execute(
            "UPDATE account_users SET providers_recid = NULL WHERE element_guid = ?;",
            (guid,),
          )
    return {"rows": [{"providers_remaining": cnt}], "rowcount": 1}

@register("urn:users:providers:soft_delete_account:1")
def _users_soft_delete_account(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    sql = """
      UPDATE account_users
      SET element_soft_deleted_at = SYSDATETIMEOFFSET()
      WHERE element_guid = ?;
    """
    return ("exec", sql, (guid,))

@register("urn:users:providers:get_user_by_email:1")
def _users_get_user_by_email(args: Dict[str, Any]):
    email = args["email"]
    sql = """
      SELECT TOP 1
        element_guid AS guid
      FROM account_users
      WHERE element_email = ?;
    """
    return ("row_one", sql, (email,))

@register("urn:users:profile:get_profile:1")
def _users_profile(args: Dict[str, Any]):
    guid = str(args["guid"])
    sql = """
      SELECT TOP 1
        v.user_guid AS guid,
        v.display_name,
        v.email,
        v.opt_in AS display_email,
        v.credits,
        v.profile_image_base64 AS profile_image,
        v.provider_name AS default_provider,
        (
          SELECT
            ap.element_name AS name,
            ap.element_display AS display
          FROM users_auth ua
          JOIN auth_providers ap ON ap.recid = ua.providers_recid
          WHERE ua.users_guid = v.user_guid
          FOR JSON PATH
        ) AS auth_providers
      FROM vw_account_user_profile v
      WHERE v.user_guid = ?;
    """
    return ("row_one", sql, (guid,))


@register("db:users:profile:get_profile:1")
def _db_users_profile(args: Dict[str, Any]):
  return _users_profile(args)


@register("urn:users:profile:set_display:1")
def _users_set_display(args: Dict[str, Any]):
    guid = args["guid"]
    display_name = args["display_name"]
    sql = """
      UPDATE account_users
      SET element_display = ?
      WHERE element_guid = ?;
    """
    return ("exec", sql, (display_name, guid))


@register("urn:users:profile:set_optin:1")
def _users_set_optin(args: Dict[str, Any]):
    guid = args["guid"]
    display_email = args["display_email"]
    sql = """
      UPDATE account_users
      SET element_optin = ?
      WHERE element_guid = ?;
    """
    return ("exec", sql, (display_email, guid))


@register("urn:users:providers:set_provider:1")
async def _users_set_provider(args: Dict[str, Any]):
  guid = args["guid"]
  provider = args["provider"]
  res = await fetch_json(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  )
  if not res.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  return await exec_query(
    "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
    (res.rows[0]["recid"], guid),
  )

@register("urn:users:profile:get_roles:1")
def _users_get_roles(args: Dict[str, Any]):
  """Fetch a user's role mask."""
  guid = args["guid"]
  sql = """
    SELECT element_roles FROM users_roles
    WHERE users_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return ("json_one", sql, (guid,))

@register("urn:users:profile:set_roles:1")
async def _users_set_roles(args: Dict[str, Any]):
  """Upsert a user's role mask."""
  guid, roles = args["guid"], int(args["roles"])
  if roles == 0:
    return await exec_query("DELETE FROM users_roles WHERE users_guid = ?;", (guid,))
  res = await exec_query(
    "UPDATE users_roles SET element_roles = ? WHERE users_guid = ?;",
    (roles, guid),
  )
  if res.rowcount == 0:
    res = await exec_query(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (guid, roles),
    )
  return res

@register("db:users:session:set_rotkey:1")
def _users_session_set_rotkey(args: Dict[str, Any]):
    guid = args["guid"]
    rotkey = args["rotkey"]
    iat = args["iat"]
    exp = args["exp"]
    sql = """
      UPDATE account_users
      SET element_rotkey = ?, element_rotkey_iat = ?, element_rotkey_exp = ?
      WHERE element_guid = ?;
    """
    return ("exec", sql, (rotkey, iat, exp, guid))

@register("db:users:session:get_rotkey:1")
def _users_session_get_rotkey(args: Dict[str, Any]):
    guid = args["guid"]
    sql = """
      SELECT TOP 1 element_rotkey AS rotkey
      FROM vw_account_user_security
      WHERE user_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return ("json_one", sql, (guid,))

@register("urn:public:links:get_home_links:1")
def _public_links_get_home_links(args: Dict[str, Any]):
    sql = """
      SELECT
        element_title AS title,
        element_url AS url
      FROM frontend_links
      ORDER BY element_sequence
      FOR JSON PATH;
    """
    return ("json_many", sql, ())

@register("urn:public:links:get_navbar_routes:1")
def _public_links_get_navbar_routes(args: Dict[str, Any]):
    mask = int(args.get("role_mask", 0))
    sql = """
      SELECT
        element_path AS path,
        element_name AS name,
        element_icon AS icon
      FROM frontend_routes
      WHERE element_roles = 0 OR (element_roles & ?) = element_roles
      ORDER BY element_sequence
      FOR JSON PATH;
    """
    return ("json_many", sql, (mask,))

# -------------------- SYSTEM ROUTES --------------------

@register("urn:system:routes:get_routes:1")
def _system_routes_get_routes(_: Dict[str, Any]):
  sql = """
    SELECT
      element_path,
      element_name,
      element_icon,
      element_sequence,
      element_roles
    FROM frontend_routes
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  return ("json_many", sql, ())

@register("urn:system:routes:upsert_route:1")
async def _system_routes_upsert_route(args: Dict[str, Any]):
  path = args["path"]
  name = args["name"]
  icon = args.get("icon")
  sequence = int(args["sequence"])
  roles = int(args["roles"])
  rc = await exec_query(
    "UPDATE frontend_routes SET element_name = ?, element_icon = ?, element_sequence = ?, element_roles = ? WHERE element_path = ?;",
    (name, icon, sequence, roles, path),
  )
  if rc.rowcount == 0:
    rc = await exec_query(
      "INSERT INTO frontend_routes (element_path, element_name, element_icon, element_sequence, element_roles) VALUES (?, ?, ?, ?, ?);",
      (path, name, icon, sequence, roles),
    )
  return rc

@register("urn:system:routes:delete_route:1")
def _system_routes_delete_route(args: Dict[str, Any]):
  path = args["path"]
  sql = "DELETE FROM frontend_routes WHERE element_path = ?;"
  return ("exec", sql, (path,))

@register("urn:public:vars:get_hostname:1")
def _public_vars_get_hostname(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS hostname
    FROM system_config
    WHERE element_key = 'hostname'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return ("json_one", sql, ())

@register("urn:public:vars:get_version:1")
def _public_vars_get_version(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS version
    FROM system_config
    WHERE element_key = 'version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return ("json_one", sql, ())

@register("urn:public:vars:get_repo:1")
def _public_vars_get_repo(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS repo
    FROM system_config
    WHERE element_key = 'repo'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return ("json_one", sql, ())

@register("urn:users:profile:set_profile_image:1")
async def _users_set_img(args: Dict[str, Any]):
  """Insert or update a user's profile image."""
  guid, image_b64, provider = args["guid"], args["image_b64"], args["provider"]
  res = await fetch_json(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  )
  if not res.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  ap_recid = res.rows[0]["recid"]
  rc = await exec_query(
    "UPDATE users_profileimg SET element_base64 = ?, providers_recid = ? WHERE users_guid = ?;",
    (image_b64, ap_recid, guid),
  )
  if rc.rowcount == 0:
    rc = await exec_query(
      "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
      (guid, image_b64, ap_recid),
    )
  return rc

@register("db:auth:session:create_session:1")
async def _auth_session_create_session(args: Dict[str, Any]):
    from uuid import uuid4
    device_guid = str(uuid4())
    access_token = args["access_token"]
    expires = args["expires"]
    fingerprint = args.get("fingerprint")
    user_agent = args.get("user_agent")
    ip_address = args.get("ip_address")
    user_guid = args["user_guid"]
    provider = args["provider"]

    async with transaction() as cur:
      await cur.execute(
        "SELECT recid FROM auth_providers WHERE element_name = ?;",
        (provider,),
      )
      row = await cur.fetchone()
      if not row:
        raise ValueError(f"Unknown auth provider: {provider}")
      provider_recid = row[0]

      await cur.execute(
        "SELECT element_guid FROM users_sessions WHERE users_guid = ?;",
        (user_guid,),
      )
      row = await cur.fetchone()
      if row:
        session_guid = row[0]
        await cur.execute(
          "UPDATE users_sessions SET element_created_at = SYSDATETIMEOFFSET() WHERE users_guid = ?;",
          (user_guid,),
        )
      else:
        session_guid = str(uuid4())
        await cur.execute(
          """
            INSERT INTO users_sessions (element_guid, users_guid, element_created_at)
            VALUES (?, ?, SYSDATETIMEOFFSET());
          """,
          (session_guid, user_guid),
        )
      await cur.execute(
        """
          INSERT INTO sessions_devices (
            element_guid, sessions_guid, providers_recid, element_token, element_token_iat, element_token_exp,
            element_device_fingerprint, element_user_agent, element_ip_last_seen
          ) VALUES (?, ?, ?, ?, SYSDATETIMEOFFSET(), ?, ?, ?, ?);
        """,
        (
          device_guid,
          session_guid,
          provider_recid,
          access_token,
          expires,
          fingerprint,
          user_agent,
          ip_address,
        ),
      )

    return {"rows": [{"session_guid": session_guid, "device_guid": device_guid}], "rowcount": 1}

@register("db:auth:session:get_by_access_token:1")
def _auth_session_get_by_access_token(args: Dict[str, Any]):
    token = args["access_token"]
    sql = """
      SELECT
        device_guid,
        session_guid,
        user_guid,
        providers_recid,
        provider_name,
        session_created_at,
        element_token AS token,
        element_token_iat AS issued_at,
        element_token_exp AS expires_at,
        element_revoked_at AS revoked_at,
        element_device_fingerprint AS device_fingerprint,
        element_user_agent AS user_agent,
        element_ip_last_seen AS ip_last_seen
      FROM vw_account_user_security
      WHERE element_token = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return ("json_one", sql, (token,))

@register("db:auth:session:update_session:1")
def _auth_session_update_session(args: Dict[str, Any]):
    token = args["access_token"]
    ip_address = args.get("ip_address")
    user_agent = args.get("user_agent")
    sql = """
      UPDATE sessions_devices
      SET element_ip_last_seen = ?, element_user_agent = ?
      WHERE element_token = ?;
    """
    return ("exec", sql, (ip_address, user_agent, token))

@register("db:auth:session:revoke_device_token:1")
def _auth_session_revoke_device_token(args: Dict[str, Any]):
  token = args["access_token"]
  sql = """
    UPDATE sessions_devices
    SET element_revoked_at = SYSDATETIMEOFFSET()
    WHERE element_token = ?;
  """
  return ("exec", sql, (token,))

@register("db:auth:session:revoke_all_device_tokens:1")
def _auth_session_revoke_all_device_tokens(args: Dict[str, Any]):
  guid = str(UUID(args["guid"]))
  sql = """
    UPDATE sd
    SET element_revoked_at = SYSDATETIMEOFFSET()
    FROM sessions_devices sd
    JOIN users_sessions us ON us.element_guid = sd.sessions_guid
    WHERE us.users_guid = ?;
  """
  return ("exec", sql, (guid,))

@register("db:auth:session:revoke_provider_tokens:1")
def _auth_session_revoke_provider_tokens(args: Dict[str, Any]):
  guid = str(UUID(args["guid"]))
  provider = args["provider"]
  sql = """
    UPDATE sd
    SET element_revoked_at = SYSDATETIMEOFFSET()
    FROM sessions_devices sd
    JOIN users_sessions us ON us.element_guid = sd.sessions_guid
    JOIN auth_providers ap ON ap.recid = sd.providers_recid
    WHERE us.users_guid = ? AND ap.element_name = ?;
  """
  return ("exec", sql, (guid, provider))

# -------------------- SYSTEM CONFIG --------------------

@register("db:system:config:get_config:1")
@register("urn:system:config:get_config:1")
def _config_get(args: Dict[str, Any]):
  key = args["key"]
  sql = """
    SELECT element_value AS value
    FROM system_config
    WHERE element_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return ("json_one", sql, (key,))

@register("db:system:config:upsert_config:1")
@register("urn:system:config:upsert_config:1")
async def _config_set(args: Dict[str, Any]):
  key = args["key"]
  value = args["value"]
  rc = await exec_query(
    "UPDATE system_config SET element_value = ? WHERE element_key = ?;",
    (value, key),
  )
  if rc.rowcount == 0:
    rc = await exec_query(
      "INSERT INTO system_config (element_key, element_value) VALUES (?, ?);",
      (key, value),
    )
  return rc

@register("db:system:config:get_configs:1")
@register("urn:system:config:get_configs:1")
def _config_list(_: Dict[str, Any]):
  sql = """
    SELECT element_key, element_value
    FROM system_config
    ORDER BY element_key
    FOR JSON PATH;
  """
  return ("json_many", sql, ())

@register("db:system:config:delete_config:1")
@register("urn:system:config:delete_config:1")
def _config_delete(args: Dict[str, Any]):
  key = args["key"]
  sql = "DELETE FROM system_config WHERE element_key = ?;"
  return ("exec", sql, (key,))


# -------------------- SECURITY ROLES --------------------

@register("db:system:roles:list:1")
def _system_roles_list(_: Dict[str, Any]):
  sql = """
    SELECT element_name AS name, element_mask AS mask, element_display AS display
    FROM system_roles
    ORDER BY element_mask
    FOR JSON PATH;
  """
  return ("json_many", sql, ())


@register("db:security:roles:upsert_role:1")
async def _security_roles_upsert_role(args: Dict[str, Any]):
  name = args["name"]
  mask = int(args["mask"])
  display = args.get("display")
  rc = await exec_query(
    "UPDATE system_roles SET element_mask = ?, element_display = ? WHERE element_name = ?;",
    (mask, display, name),
  )
  if rc.rowcount == 0:
    rc = await exec_query(
      "INSERT INTO system_roles (element_name, element_mask, element_display) VALUES (?, ?, ?);",
      (name, mask, display),
    )
  return rc


@register("db:security:roles:delete_role:1")
async def _security_roles_delete_role(args: Dict[str, Any]):
  name = args["name"]
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask;
    DELETE FROM system_roles WHERE element_name = ?;
  """
  rc = await exec_query(sql, (name, name))
  return rc


@register("db:security:roles:get_role_members:1")
def _security_roles_get_members(args: Dict[str, Any]):
  role = args["role"]
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ur.element_roles & sr.element_mask) > 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  return ("json_many", sql, (role,))


@register("db:security:roles:get_role_non_members:1")
def _security_roles_get_non_members(args: Dict[str, Any]):
  role = args["role"]
  sql = """
    SELECT au.element_guid AS guid, au.element_display AS display_name
    FROM account_users au
    LEFT JOIN users_roles ur ON au.element_guid = ur.users_guid
    JOIN system_roles sr ON sr.element_name = ?
    WHERE (ISNULL(ur.element_roles, 0) & sr.element_mask) = 0
    ORDER BY au.element_display
    FOR JSON PATH;
  """
  return ("json_many", sql, (role,))


@register("db:security:roles:add_role_member:1")
def _security_roles_add_member(args: Dict[str, Any]):
  role = args["role"]
  user_guid = args["user_guid"]
  sql = """
    MERGE users_roles AS ur
    USING (SELECT ? AS users_guid, element_mask FROM system_roles WHERE element_name = ?) AS src
    ON ur.users_guid = src.users_guid
    WHEN MATCHED THEN UPDATE SET element_roles = ur.element_roles | src.element_mask
    WHEN NOT MATCHED THEN INSERT (users_guid, element_roles) VALUES (src.users_guid, src.element_mask);
  """
  return ("exec", sql, (user_guid, role))


@register("db:security:roles:remove_role_member:1")
def _security_roles_remove_member(args: Dict[str, Any]):
  role = args["role"]
  user_guid = args["user_guid"]
  sql = """
    DECLARE @mask BIGINT;
    SELECT @mask = element_mask FROM system_roles WHERE element_name = ?;
    UPDATE users_roles SET element_roles = element_roles & ~@mask WHERE users_guid = ?;
    DELETE FROM users_roles WHERE users_guid = ? AND element_roles = 0;
  """
  return ("exec", sql, (role, user_guid, user_guid))

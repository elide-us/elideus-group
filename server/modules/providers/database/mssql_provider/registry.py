# providers/database/mssql_provider/registry.py
from typing import Any, Awaitable, Callable, Dict, Tuple
from uuid import UUID, uuid5, NAMESPACE_URL
from ... import DBResult, DbRunMode
from .logic import init_pool, close_pool, transaction
from .db_helpers import fetch_rows, fetch_json, exec_query
import logging

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
      JOIN users_auth ua ON ua.users_guid = v.user_guid AND ua.element_linked = 1
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      WHERE ap.element_name = ? AND ua.element_identifier = ?;
    """
    return (DbRunMode.ROW_ONE, sql, (provider, identifier))

@register("db:users:providers:get_by_provider_identifier:1")
def _db_users_select(provider_args: Dict[str, Any]):
  return _users_select(provider_args)

@register("urn:users:providers:get_any_by_provider_identifier:1")
def _users_select_any(provider_args: Dict[str, Any]):
    identifier = str(UUID(provider_args["provider_identifier"]))
    sql = """
      SELECT TOP 1
        au.element_guid AS guid,
        au.element_soft_deleted_at
      FROM users_auth ua
      JOIN account_users au ON au.element_guid = ua.users_guid
      WHERE ua.element_identifier = ?;
    """
    return (DbRunMode.ROW_ONE, sql, (identifier,))

@register("db:users:providers:get_any_by_provider_identifier:1")
def _db_users_select_any(provider_args: Dict[str, Any]):
  return _users_select_any(provider_args)

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

    dup = await fetch_json(
      "SELECT users_guid FROM users_auth WHERE element_identifier = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
      (identifier,),
    )
    if dup.rows:
      existing_guid = dup.rows[0]["users_guid"]
      await exec_query(
        "UPDATE users_auth SET element_linked = 1, providers_recid = ? WHERE element_identifier = ?;",
        (ap_recid, identifier),
      )
      await exec_query(
        "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
        (ap_recid, existing_guid),
      )
      sel = _users_select({"provider": provider, "provider_identifier": identifier})
      return await fetch_rows(sel[1], sel[2], one=True)

    async with transaction() as cur:
        await cur.execute(
            """
            INSERT INTO account_users (element_guid, element_email, element_display, providers_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (new_guid, provider_email, provider_displayname, ap_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
        )
        await cur.execute(
            "INSERT INTO users_auth (users_guid, providers_recid, element_identifier, element_linked) VALUES (?, ?, ?, 1);",
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

@register("db:users:providers:create_from_provider:1")
async def _db_users_insert(args: Dict[str, Any]):
  return await _users_insert(args)

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
      """
      MERGE users_auth AS target
      USING (SELECT ? AS users_guid, ? AS providers_recid, ? AS element_identifier) AS source
      ON target.element_identifier = source.element_identifier
      WHEN MATCHED THEN
        UPDATE SET users_guid = source.users_guid, providers_recid = source.providers_recid, element_linked = 1
      WHEN NOT MATCHED THEN
        INSERT (users_guid, providers_recid, element_identifier, element_linked)
        VALUES (source.users_guid, source.providers_recid, source.element_identifier, 1);
      """,
      (guid, ap_recid, identifier)
    )
    return rc

@register("db:users:providers:link_provider:1")
async def _db_users_link_provider(args: Dict[str, Any]):
  return await _users_link_provider(args)

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
        UPDATE ua
        SET ua.element_linked = 0
        FROM users_auth ua
        JOIN auth_providers ap ON ap.recid = ua.providers_recid
        WHERE ua.users_guid = ? AND ap.element_name = ?;
        """,
        (guid, provider)
      )
      await cur.execute(
        "SELECT COUNT(*) AS cnt FROM users_auth WHERE users_guid = ? AND element_linked = 1;",
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
          "UPDATE account_users SET providers_recid = NULL, element_display = '', element_email = '' WHERE element_guid = ?;",
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

@register("db:users:providers:unlink_provider:1")
async def _db_users_unlink_provider(args: Dict[str, Any]):
  return await _users_unlink_provider(args)

@register("urn:users:providers:soft_delete_account:1")
def _users_soft_delete_account(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    sql = """
      UPDATE account_users
      SET element_soft_deleted_at = SYSDATETIMEOFFSET()
      WHERE element_guid = ?;
    """
    return (DbRunMode.EXEC, sql, (guid,))

@register("db:users:providers:soft_delete_account:1")
def _db_users_soft_delete_account(args: Dict[str, Any]):
  return _users_soft_delete_account(args)

@register("urn:users:providers:get_user_by_email:1")
def _users_get_user_by_email(args: Dict[str, Any]):
    email = args["email"]
    sql = """
      SELECT TOP 1
        element_guid AS guid
      FROM account_users
      WHERE element_email = ?;
    """
    return (DbRunMode.ROW_ONE, sql, (email,))

@register("db:users:providers:get_user_by_email:1")
def _db_users_get_user_by_email(args: Dict[str, Any]):
  return _users_get_user_by_email(args)

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
          WHERE ua.users_guid = v.user_guid AND ua.element_linked = 1
          FOR JSON PATH
        ) AS auth_providers
      FROM vw_account_user_profile v
      WHERE v.user_guid = ?;
    """
    return (DbRunMode.ROW_ONE, sql, (guid,))

@register("urn:auth:providers:unlink_last_provider:1")
def _auth_unlink_last_provider(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    provider = args["provider"]
    sql = "EXEC auth_unlink_last_provider @guid=?, @provider=?;"
    return (DbRunMode.EXEC, sql, (guid, provider))

@register("db:auth:providers:unlink_last_provider:1")
def _db_auth_unlink_last_provider(args: Dict[str, Any]):
  return _auth_unlink_last_provider(args)

@register("urn:auth:microsoft:oauth_relink:1")
def _auth_ms_oauth_relink(args: Dict[str, Any]):
    identifier = str(UUID(args["provider_identifier"]))
    email = args.get("email")
    display = args.get("display_name")
    img = args.get("profile_image", "")
    sql = "EXEC auth_oauth_relink @provider='microsoft', @identifier=?, @email=?, @display=?, @image=?;"
    return (DbRunMode.ROW_ONE, sql, (identifier, email, display, img))

@register("db:auth:microsoft:oauth_relink:1")
def _db_auth_ms_oauth_relink(args: Dict[str, Any]):
  return _auth_ms_oauth_relink(args)

@register("urn:auth:google:oauth_relink:1")
def _auth_google_oauth_relink(args: Dict[str, Any]):
    identifier = str(UUID(args["provider_identifier"]))
    email = args.get("email")
    display = args.get("display_name")
    img = args.get("profile_image", "")
    sql = "EXEC auth_oauth_relink @provider='google', @identifier=?, @email=?, @display=?, @image=?;"
    return (DbRunMode.ROW_ONE, sql, (identifier, email, display, img))

@register("db:auth:google:oauth_relink:1")
def _db_auth_google_oauth_relink(args: Dict[str, Any]):
  return _auth_google_oauth_relink(args)

@register("urn:auth:discord:oauth_relink:1")
def _auth_discord_oauth_relink(args: Dict[str, Any]):
    raw_id = args["provider_identifier"]
    identifier = str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{raw_id}"))))
    email = args.get("email")
    display = args.get("display_name")
    img = args.get("profile_image", "")
    sql = "EXEC auth_oauth_relink @provider='discord', @identifier=?, @email=?, @display=?, @image=?;"
    return (DbRunMode.ROW_ONE, sql, (identifier, email, display, img))

@register("db:auth:discord:oauth_relink:1")
def _db_auth_discord_oauth_relink(args: Dict[str, Any]):
  return _auth_discord_oauth_relink(args)

@register("urn:auth:discord:get_security:1")
def _auth_discord_get_security(args: Dict[str, Any]):
  raw_id = args["discord_id"]
  identifier = str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{raw_id}"))))
  sql = """
    SELECT TOP 1
      v.user_guid,
      v.user_roles
    FROM vw_user_session_security v
    JOIN users_auth ua ON ua.users_guid = v.user_guid
    JOIN auth_providers ap ON ap.recid = ua.providers_recid
    WHERE ap.element_name = 'discord' AND ua.element_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, (identifier,))

@register("db:auth:discord:get_security:1")
def _db_auth_discord_get_security(args: Dict[str, Any]):
  return _auth_discord_get_security(args)


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
    return (DbRunMode.EXEC, sql, (display_name, guid))


@register("db:users:profile:set_display:1")
def _db_users_set_display(args: Dict[str, Any]):
  return _users_set_display(args)


@register("urn:support:users:set_credits:1")
def _support_users_set_credits(args: Dict[str, Any]):
  guid = args["guid"]
  credits = args["credits"]
  sql = """
    UPDATE users_credits
    SET element_credits = ?
    WHERE users_guid = ?;
  """
  return (DbRunMode.EXEC, sql, (credits, guid))


@register("db:support:users:set_credits:1")
def _db_support_users_set_credits(args: Dict[str, Any]):
  return _support_users_set_credits(args)


# -------------------- STORAGE CACHE --------------------

@register("db:storage:cache:list:1")
def _storage_cache_list(args: Dict[str, Any]):
  user_guid = args["user_guid"]
  sql = """
    SELECT
      usc.element_path AS path,
      usc.element_filename AS filename,
      st.element_mimetype AS content_type,
      usc.element_url AS url,
      usc.element_public AS [public]
    FROM users_storage_cache usc
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.users_guid = ? AND usc.element_deleted = 0
    ORDER BY usc.element_path, usc.element_filename
    FOR JSON PATH;
  """
  return (DbRunMode.JSON_MANY, sql, (user_guid,))


@register("db:storage:cache:replace_user:1")
async def _storage_cache_replace_user(args: Dict[str, Any]):
  user_guid = args["user_guid"]
  items: list[Dict[str, Any]] = args.get("items", [])
  async with transaction() as cur:
    await cur.execute("DELETE FROM users_storage_cache WHERE users_guid = ?;", (user_guid,))
    for item in items:
      path = item.get("path", "")
      filename = item.get("filename", "")
      mimetype = item.get("content_type", "application/octet-stream")
      res = await fetch_json(
        "SELECT recid FROM storage_types WHERE element_mimetype = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
        (mimetype,),
      )
      if not res.rows:
        raise ValueError(f"Unknown storage mimetype: {mimetype}")
      type_recid = res.rows[0]["recid"]
      await cur.execute(
        """INSERT INTO users_storage_cache
          (users_guid, types_recid, element_path, element_filename, element_public, element_modified_on, element_deleted)
          VALUES (?, ?, ?, ?, ?, NULL, 0);""",
        (user_guid, type_recid, path, filename, item.get("public", 0)),
      )
  return DBResult(rows=[], rowcount=len(items))


@register("db:storage:cache:upsert:1")
async def _storage_cache_upsert(args: Dict[str, Any]):
  user_guid = args["user_guid"]
  path = args.get("path", "")
  filename = args.get("filename", "")
  mimetype = args.get("content_type", "application/octet-stream")
  public = args.get("public", 0)
  from datetime import datetime
  created_on = args.get("created_on")
  if created_on is None:
    created_on = datetime.utcnow()
  modified_on = args.get("modified_on")
  url = args.get("url")
  reported = args.get("reported", 0)
  moderation_recid = args.get("moderation_recid")
  res = await fetch_json(
    "SELECT recid FROM storage_types WHERE element_mimetype = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (mimetype,),
  )
  if not res.rows:
    if mimetype == "path/folder":
      await exec_query(
        """
        MERGE storage_types AS target
        USING (SELECT 16 AS recid, 'path/folder' AS element_mimetype, 'Folder' AS element_displaytype) AS src
        ON target.element_mimetype = src.element_mimetype
        WHEN NOT MATCHED THEN
          INSERT (recid, element_mimetype, element_displaytype)
          VALUES (src.recid, src.element_mimetype, src.element_displaytype);
        """,
        (),
      )
      res = await fetch_json(
        "SELECT recid FROM storage_types WHERE element_mimetype = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
        (mimetype,),
      )
    else:
      res = await fetch_json(
        "SELECT recid FROM storage_types WHERE element_mimetype = 'application/octet-stream' FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
        (),
      )
  type_recid = res.rows[0]["recid"] if res.rows else (16 if mimetype == "path/folder" else 1)
  sql = """
    MERGE users_storage_cache AS target
    USING (SELECT ? AS users_guid, ? AS types_recid, ? AS element_path, ? AS element_filename,
                  ? AS element_public, ? AS element_created_on, ? AS element_modified_on,
                  ? AS element_deleted, ? AS element_url, ? AS element_reported, ? AS moderation_recid) AS src
    ON target.users_guid = src.users_guid AND target.element_path = src.element_path AND target.element_filename = src.element_filename
    WHEN MATCHED THEN UPDATE SET
      types_recid = src.types_recid,
      element_public = src.element_public,
      element_created_on = src.element_created_on,
      element_modified_on = src.element_modified_on,
      element_deleted = src.element_deleted,
      element_url = src.element_url,
      element_reported = src.element_reported,
      moderation_recid = src.moderation_recid
    WHEN NOT MATCHED THEN
      INSERT (users_guid, types_recid, element_path, element_filename, element_public,
              element_created_on, element_modified_on, element_deleted, element_url,
              element_reported, moderation_recid)
      VALUES (src.users_guid, src.types_recid, src.element_path, src.element_filename,
              src.element_public, src.element_created_on, src.element_modified_on,
              src.element_deleted, src.element_url, src.element_reported, src.moderation_recid);
  """
  params = (
    user_guid,
    type_recid,
    path,
    filename,
    public,
    created_on,
    modified_on,
    0,
    url,
    reported,
    moderation_recid,
  )
  rc = await exec_query(sql, params)
  if rc.rowcount == 0:
    logging.error(
      "[MSSQL] storage_cache_upsert affected 0 rows for %s/%s",
      path or ".",
      filename,
    )
  return rc


@register("db:storage:cache:delete:1")
def _storage_cache_delete(args: Dict[str, Any]):
  user_guid = args["user_guid"]
  path = args.get("path", "")
  filename = args.get("filename", "")
  sql = """
    DELETE FROM users_storage_cache
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return (DbRunMode.EXEC, sql, (user_guid, path, filename))


@register("db:storage:cache:delete_folder:1")
def _storage_cache_delete_folder(args: Dict[str, Any]):
  user_guid = args["user_guid"]
  path = args.get("path", "").lstrip("/")
  parent, name = path.rsplit("/", 1) if "/" in path else ("", path)
  like = f"{path}/%" if path else "%"
  sql = """
    DELETE FROM users_storage_cache
    WHERE users_guid = ? AND (
      (element_path = ? AND element_filename = ?)
      OR element_path = ?
      OR element_path LIKE ?
    );
  """
  return (DbRunMode.EXEC, sql, (user_guid, parent, name, path, like))


@register("db:storage:cache:set_public:1")
def _storage_cache_set_public(args: Dict[str, Any]):
  guid = str(UUID(args["user_guid"]))
  path = args.get("path", "")
  filename = args.get("filename", "")
  public = 1 if args.get("public") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_public = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return (DbRunMode.EXEC, sql, (public, guid, path, filename))


@register("db:storage:files:set_gallery:1")
def _storage_files_set_gallery(args: Dict[str, Any]):
  guid = str(UUID(args["user_guid"]))
  name = args.get("name", "")
  path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
  gallery = 1 if args.get("gallery") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_public = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return (DbRunMode.EXEC, sql, (gallery, guid, path, filename))


@register("db:storage:cache:set_reported:1")
def _storage_cache_set_reported(args: Dict[str, Any]):
  guid = str(UUID(args["user_guid"]))
  path = args.get("path", "")
  filename = args.get("filename", "")
  reported = 1 if args.get("reported") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_reported = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return (DbRunMode.EXEC, sql, (reported, guid, path, filename))


@register("db:storage:cache:list_public:1")
def _storage_cache_list_public(_: Dict[str, Any]):
  sql = """
    SELECT usc.users_guid AS user_guid,
           au.element_display AS display_name,
           usc.element_path AS path,
           usc.element_filename AS name,
           usc.element_url AS url,
           st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN account_users au ON au.element_guid = usc.users_guid
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.element_public = 1 AND usc.element_deleted = 0 AND ISNULL(usc.element_reported,0) = 0
    ORDER BY usc.element_created_on;
  """
  return (DbRunMode.ROW_MANY, sql, ())


@register("db:public:gallery:get_public_files:1")
def _public_gallery_get_public_files(_: Dict[str, Any]):
  sql = """
    SELECT usc.users_guid AS user_guid,
           au.element_display AS display_name,
           usc.element_path AS path,
           usc.element_filename AS name,
           usc.element_url AS url,
           st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN account_users au ON au.element_guid = usc.users_guid
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.element_public = 1 AND usc.element_deleted = 0 AND ISNULL(usc.element_reported,0) = 0
    ORDER BY usc.element_created_on;
  """
  return (DbRunMode.ROW_MANY, sql, ())


@register("db:storage:cache:list_reported:1")
def _storage_cache_list_reported(_: Dict[str, Any]):
  sql = """
    SELECT usc.users_guid AS user_guid,
           usc.element_path AS path,
           usc.element_filename AS name,
           usc.element_url AS url,
           st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.element_reported = 1 AND usc.element_deleted = 0
    ORDER BY usc.element_created_on;
  """
  return (DbRunMode.ROW_MANY, sql, ())


@register("db:storage:cache:count_rows:1")
def _storage_cache_count_rows(_: Dict[str, Any]):
  sql = """
    SELECT COUNT(*) AS count
    FROM users_storage_cache
    WHERE element_deleted = 0
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, ())


@register("urn:users:profile:set_optin:1")
def _users_set_optin(args: Dict[str, Any]):
    guid = args["guid"]
    display_email = args["display_email"]
    sql = """
      UPDATE account_users
      SET element_optin = ?
      WHERE element_guid = ?;
    """
    return (DbRunMode.EXEC, sql, (display_email, guid))

@register("db:users:profile:set_optin:1")
def _db_users_set_optin(args: Dict[str, Any]):
  return _users_set_optin(args)


@register("urn:users:profile:update_if_unedited:1")
async def _users_update_if_unedited(args: Dict[str, Any]):
  guid = str(UUID(args["guid"]))
  email = args.get("email")
  display = args.get("display_name")
  res = await exec_query(
    """
    UPDATE account_users
    SET element_email = ?, element_display = ?
    WHERE element_guid = ? AND (element_email <> ? OR element_display <> ?);
    """,
    (email, display, guid, email, display),
  )
  if res.rowcount > 0:
    return await fetch_json(
      """
      SELECT element_display AS display_name, element_email AS email
      FROM account_users
      WHERE element_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
      """,
      (guid,),
    )
  return DBResult()

@register("db:users:profile:update_if_unedited:1")
async def _db_users_update_if_unedited(args: Dict[str, Any]):
  return await _users_update_if_unedited(args)


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

@register("db:users:providers:set_provider:1")
async def _db_users_set_provider(args: Dict[str, Any]):
  return await _users_set_provider(args)

@register("urn:users:profile:get_roles:1")
def _users_get_roles(args: Dict[str, Any]):
  """Fetch a user's role mask."""
  guid = args["guid"]
  sql = """
    SELECT element_roles FROM users_roles
    WHERE users_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, (guid,))

@register("db:users:profile:get_roles:1")
def _db_users_get_roles(args: Dict[str, Any]):
  return _users_get_roles(args)

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

@register("db:users:profile:set_roles:1")
async def _db_users_set_roles(args: Dict[str, Any]):
  return await _users_set_roles(args)

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
    return (DbRunMode.EXEC, sql, (rotkey, iat, exp, guid))

@register("db:users:session:get_rotkey:1")
def _users_session_get_rotkey(args: Dict[str, Any]):
  guid = args["guid"]
  sql = """
      SELECT
        au.element_rotkey AS rotkey,
        ap.element_name AS provider_name
      FROM account_users AS au
      LEFT JOIN auth_providers AS ap ON au.providers_recid = ap.recid
      WHERE au.element_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
  return (DbRunMode.JSON_ONE, sql, (guid,))

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
    return (DbRunMode.JSON_MANY, sql, ())

@register("db:public:links:get_home_links:1")
def _db_public_links_get_home_links(args: Dict[str, Any]):
  return _public_links_get_home_links(args)

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
    return (DbRunMode.JSON_MANY, sql, (mask,))

@register("db:public:links:get_navbar_routes:1")
def _db_public_links_get_navbar_routes(args: Dict[str, Any]):
  return _public_links_get_navbar_routes(args)

# -------------------- SERVICE ROUTES --------------------

@register("urn:service:routes:get_routes:1")
def _service_routes_get_routes(_: Dict[str, Any]):
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
  return (DbRunMode.JSON_MANY, sql, ())

@register("db:service:routes:get_routes:1")
def _db_service_routes_get_routes(args: Dict[str, Any]):
  return _service_routes_get_routes(args)

@register("urn:service:routes:upsert_route:1")
async def _service_routes_upsert_route(args: Dict[str, Any]):
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

@register("db:service:routes:upsert_route:1")
async def _db_service_routes_upsert_route(args: Dict[str, Any]):
  return await _service_routes_upsert_route(args)

@register("urn:service:routes:delete_route:1")
def _service_routes_delete_route(args: Dict[str, Any]):
  path = args["path"]
  sql = "DELETE FROM frontend_routes WHERE element_path = ?;"
  return (DbRunMode.EXEC, sql, (path,))

@register("db:service:routes:delete_route:1")
def _db_service_routes_delete_route(args: Dict[str, Any]):
  return _service_routes_delete_route(args)

@register("urn:public:vars:get_hostname:1")
def _public_vars_get_hostname(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS hostname
    FROM system_config
    WHERE element_key = 'hostname'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, ())

@register("db:public:vars:get_hostname:1")
def _db_public_vars_get_hostname(args: Dict[str, Any]):
  return _public_vars_get_hostname(args)

@register("urn:public:vars:get_version:1")
def _public_vars_get_version(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS version
    FROM system_config
    WHERE element_key = 'version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, ())

@register("db:public:vars:get_version:1")
def _db_public_vars_get_version(args: Dict[str, Any]):
  return _public_vars_get_version(args)

@register("urn:public:vars:get_repo:1")
def _public_vars_get_repo(args: Dict[str, Any]):
  sql = """
    SELECT element_value AS repo
    FROM system_config
    WHERE element_key = 'repo'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return (DbRunMode.JSON_ONE, sql, ())

@register("db:public:vars:get_repo:1")
def _db_public_vars_get_repo(args: Dict[str, Any]):
  return _public_vars_get_repo(args)

@register("urn:public:users:get_profile:1")
def _public_users_get_profile(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    sql = """
      SELECT TOP 1
        au.element_display AS display_name,
        CASE WHEN au.element_optin = 1 THEN au.element_email ELSE NULL END AS email,
        up.element_base64 AS profile_image
      FROM account_users au
      LEFT JOIN users_profileimg up ON up.users_guid = au.element_guid
      WHERE au.element_guid = ?;
    """
    return (DbRunMode.ROW_ONE, sql, (guid,))

@register("db:public:users:get_profile:1")
def _db_public_users_get_profile(args: Dict[str, Any]):
  return _public_users_get_profile(args)

@register("urn:public:users:get_published_files:1")
def _public_users_get_published_files(args: Dict[str, Any]):
    guid = str(UUID(args["guid"]))
    sql = """
      SELECT
        usc.element_path AS path,
        usc.element_filename AS filename,
        usc.element_url AS url,
        st.element_mimetype AS content_type
      FROM users_storage_cache usc
      JOIN storage_types st ON st.recid = usc.types_recid
      WHERE usc.users_guid = ? AND usc.element_public = 1 AND usc.element_deleted = 0 AND ISNULL(usc.element_reported,0) = 0
      ORDER BY usc.element_created_on;
    """
    return (DbRunMode.ROW_MANY, sql, (guid,))

@register("db:public:users:get_published_files:1")
def _db_public_users_get_published_files(args: Dict[str, Any]):
  return _public_users_get_published_files(args)

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

@register("db:users:profile:set_profile_image:1")
async def _db_users_set_img(args: Dict[str, Any]):
  return await _users_set_img(args)

@register("db:auth:session:create_session:1")
async def _auth_session_create_session(args: Dict[str, Any]):
    from uuid import uuid4
    access_token = args["access_token"]
    expires = args["expires"]
    fingerprint = args.get("fingerprint")
    user_agent = args.get("user_agent")
    ip_address = args.get("ip_address")
    user_guid = args["user_guid"]
    provider = args["provider"]

    if not fingerprint:
      raise ValueError("Missing device fingerprint")

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
        "SELECT element_guid FROM sessions_devices WHERE sessions_guid = ? AND element_device_fingerprint = ?;",
        (session_guid, fingerprint),
      )
      row = await cur.fetchone()
      if row:
        device_guid = row[0]
        await cur.execute(
          """
            UPDATE sessions_devices
            SET element_token = ?, element_token_iat = SYSDATETIMEOFFSET(), element_token_exp = ?,
                element_user_agent = ?, element_ip_last_seen = ?, element_revoked_at = NULL
            WHERE element_guid = ?;
          """,
          (access_token, expires, user_agent, ip_address, device_guid),
        )
      else:
        device_guid = str(uuid4())
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
        session_created_on AS session_created_at,
        element_token AS token,
        element_token_iat AS issued_at,
        element_token_exp AS expires_at,
        element_revoked_at AS revoked_at,
        element_device_fingerprint AS device_fingerprint,
        element_user_agent AS user_agent,
        element_ip_last_seen AS ip_last_seen,
        user_roles AS roles
      FROM vw_user_session_security
      WHERE element_token = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
    """
    return (DbRunMode.JSON_ONE, sql, (token,))

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
  return (DbRunMode.EXEC, sql, (ip_address, user_agent, token))

@register("db:auth:session:update_device_token:1")
def _auth_session_update_device_token(args: Dict[str, Any]):
  from uuid import UUID
  device_guid = str(UUID(args["device_guid"]))
  token = args["access_token"]
  sql = """
    UPDATE sessions_devices
    SET element_token = ?
    WHERE element_guid = ?;
  """
  return (DbRunMode.EXEC, sql, (token, device_guid))

@register("db:auth:session:revoke_device_token:1")
def _auth_session_revoke_device_token(args: Dict[str, Any]):
  token = args["access_token"]
  sql = """
    UPDATE sessions_devices
    SET element_revoked_at = SYSDATETIMEOFFSET()
    WHERE element_token = ?;
  """
  return (DbRunMode.EXEC, sql, (token,))

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
  return (DbRunMode.EXEC, sql, (guid,))

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
  return (DbRunMode.EXEC, sql, (guid, provider))

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
  return (DbRunMode.JSON_ONE, sql, (key,))

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
  return (DbRunMode.JSON_MANY, sql, ())

@register("db:system:config:delete_config:1")
@register("urn:system:config:delete_config:1")
def _config_delete(args: Dict[str, Any]):
  key = args["key"]
  sql = "DELETE FROM system_config WHERE element_key = ?;"
  return (DbRunMode.EXEC, sql, (key,))


# -------------------- SECURITY ROLES --------------------

@register("db:system:roles:list:1")
def _system_roles_list(_: Dict[str, Any]):
  sql = """
    SELECT element_name AS name, element_mask AS mask, element_display AS display
    FROM system_roles
    ORDER BY element_mask
    FOR JSON PATH;
  """
  return (DbRunMode.JSON_MANY, sql, ())


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
  return (DbRunMode.JSON_MANY, sql, (role,))


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
  return (DbRunMode.JSON_MANY, sql, (role,))


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
  return (DbRunMode.EXEC, sql, (user_guid, role))


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
  return (DbRunMode.EXEC, sql, (role, user_guid, user_guid))

@register("db:assistant:personas:get_by_name:1")
def _assistant_personas_get_by_name(args: Dict[str, Any]):
  name = args["name"]
  sql = """
    SELECT
      ap.recid,
      ap.element_prompt AS instructions,
      ap.element_tokens,
      ap.models_recid,
      am.element_name AS model
    FROM assistant_personas ap
    JOIN assistant_models am ON am.recid = ap.models_recid
    WHERE ap.element_name = ?;
  """
  return (DbRunMode.ROW_ONE, sql, (name,))

@register("urn:assistant:models:list:1")
def _assistant_models_list(_: Dict[str, Any]):
  sql = """
    SELECT
      recid,
      element_name AS name
    FROM assistant_models
    ORDER BY element_name
    FOR JSON PATH;
  """
  return (DbRunMode.JSON_MANY, sql, ())

@register("db:assistant:models:list:1")
def _db_assistant_models_list(args: Dict[str, Any]):
  return _assistant_models_list(args)

@register("urn:assistant:personas:list:1")
def _assistant_personas_list(_: Dict[str, Any]):
  sql = """
    SELECT
      ap.recid,
      ap.element_name AS name,
      ap.element_prompt AS prompt,
      ap.element_tokens AS tokens,
      ap.models_recid,
      am.element_name AS model
    FROM assistant_personas ap
    JOIN assistant_models am ON am.recid = ap.models_recid
    ORDER BY ap.element_name
    FOR JSON PATH;
  """
  return (DbRunMode.JSON_MANY, sql, ())

@register("db:assistant:personas:list:1")
def _db_assistant_personas_list(args: Dict[str, Any]):
  return _assistant_personas_list(args)

@register("urn:assistant:personas:upsert:1")
async def _assistant_personas_upsert(args: Dict[str, Any]):
  recid = args.get("recid")
  name = args["name"]
  prompt = args["prompt"]
  tokens = int(args["tokens"])
  models_recid = int(args["models_recid"])
  if recid is not None:
    rc = await exec_query(
      """
        UPDATE assistant_personas
        SET element_name = ?,
            element_prompt = ?,
            element_tokens = ?,
            models_recid = ?,
            element_modified_on = SYSUTCDATETIME()
        WHERE recid = ?;
      """,
      (name, prompt, tokens, models_recid, recid),
    )
    if rc.rowcount:
      return rc
  rc = await exec_query(
    """
      UPDATE assistant_personas
      SET element_prompt = ?,
          element_tokens = ?,
          models_recid = ?,
          element_modified_on = SYSUTCDATETIME()
      WHERE element_name = ?;
    """,
    (prompt, tokens, models_recid, name),
  )
  if rc.rowcount:
    return rc
  return await exec_query(
    """
      INSERT INTO assistant_personas (
        element_name,
        element_prompt,
        element_tokens,
        models_recid
      ) VALUES (?, ?, ?, ?);
    """,
    (name, prompt, tokens, models_recid),
  )

@register("db:assistant:personas:upsert:1")
async def _db_assistant_personas_upsert(args: Dict[str, Any]):
  return await _assistant_personas_upsert(args)

@register("urn:assistant:personas:delete:1")
def _assistant_personas_delete(args: Dict[str, Any]):
  recid = args.get("recid")
  name = args.get("name")
  if recid is not None:
    sql = "DELETE FROM assistant_personas WHERE recid = ?;"
    params = (recid,)
  elif name is not None:
    sql = "DELETE FROM assistant_personas WHERE element_name = ?;"
    params = (name,)
  else:
    raise ValueError("Missing identifier for persona delete")
  return (DbRunMode.EXEC, sql, params)

@register("db:assistant:personas:delete:1")
def _db_assistant_personas_delete(args: Dict[str, Any]):
  return _assistant_personas_delete(args)

@register("db:assistant:models:get_by_name:1")
def _assistant_models_get_by_name(args: Dict[str, Any]):
  name = args["name"]
  sql = """
    SELECT recid FROM assistant_models WHERE element_name = ?;
  """
  return (DbRunMode.ROW_ONE, sql, (name,))

@register("db:assistant:conversations:insert:1")
def _assistant_conversations_insert(args: Dict[str, Any]):
  personas_recid = args["personas_recid"]
  models_recid = args["models_recid"]
  guild_id = args.get("guild_id")
  channel_id = args.get("channel_id")
  user_id = args.get("user_id")
  input_data = args.get("input_data")
  output_data = args.get("output_data")
  tokens = args.get("tokens")
  sql = """
    INSERT INTO assistant_conversations (
      personas_recid,
      models_recid,
      element_guild_id,
      element_channel_id,
      element_user_id,
      element_input,
      element_output,
      element_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    SELECT SCOPE_IDENTITY() AS recid;
  """
  return (
    DbRunMode.ROW_ONE,
    sql,
    (
      personas_recid,
      models_recid,
      guild_id,
      channel_id,
      user_id,
      input_data,
      output_data,
      tokens,
    ),
  )

@register("db:assistant:conversations:update_output:1")
def _assistant_conversations_update_output(args: Dict[str, Any]):
  recid = args["recid"]
  output_data = args.get("output_data")
  sql = """
    UPDATE assistant_conversations
    SET element_output = ?
    WHERE recid = ?;
  """
  return (DbRunMode.EXEC, sql, (output_data, recid))

@register("db:assistant:conversations:list_by_time:1")
def _assistant_conversations_list_by_time(args: Dict[str, Any]):
  personas_recid = args["personas_recid"]
  start = args["start"]
  end = args["end"]
  sql = """
    SELECT recid,
           element_guild_id,
           element_channel_id,
           element_user_id,
           element_input,
           element_output,
           element_tokens,
           element_created_on,
           element_modified_on,
           models_recid
    FROM assistant_conversations
    WHERE personas_recid = ? AND element_created_on BETWEEN ? AND ?
    ORDER BY element_created_on;
  """
  return (DbRunMode.JSON_MANY, sql, (personas_recid, start, end))

"""MSSQL implementations for identity providers query registry services."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_one, transaction

from .models import (
  CreateFromProviderRequestPayload,
  GetAnyByProviderIdentifierRequestPayload,
  GetByProviderIdentifierRequestPayload,
  GetUserByEmailRequestPayload,
  LinkProviderRequestPayload,
  RelinkProviderRequestPayload,
  SetProviderRequestPayload,
  SoftDeleteAccountRequestPayload,
  UnlinkLastProviderRequestPayload,
  UnlinkProviderRequestPayload,
)

__all__ = [
  "create_from_provider",
  "get_any_by_provider_identifier",
  "get_by_provider_identifier",
  "get_user_by_email",
  "link_provider",
  "relink_provider",
  "set_provider",
  "soft_delete_account",
  "unlink_last_provider",
  "unlink_provider",
]


def _normalize_provider_identifier(identifier: str) -> str:
  try:
    return str(UUID(identifier))
  except (TypeError, ValueError):
    raise ValueError("provider_identifier must be a valid UUID") from None


def _normalize_guid(guid: str) -> str:
  try:
    return str(UUID(guid))
  except (TypeError, ValueError):
    raise ValueError("guid must be a valid UUID") from None


def _normalize_discord_identifier(discord_id: str) -> str:
  return str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{discord_id}"))))


async def _get_auth_provider_recid(provider: str, *, cursor=None) -> int:
  if cursor is not None:
    await cursor.execute(
      "SELECT recid FROM auth_providers WHERE element_name = ?;",
      (provider,),
    )
    row = await cursor.fetchone()
    if not row:
      raise ValueError(f"Unknown auth provider: {provider}")
    return row[0]
  response = await run_json_one(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  )
  if not response.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  return response.rows[0]["recid"]


async def get_by_provider_identifier(
  args: GetByProviderIdentifierRequestPayload,
) -> DBResponse:
  provider = args["provider"]
  identifier = _normalize_provider_identifier(args["provider_identifier"])
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
    WHERE ap.element_name = ? AND ua.element_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (provider, identifier))
  return DBResponse(payload=response.payload)


async def get_any_by_provider_identifier(
  args: GetAnyByProviderIdentifierRequestPayload,
) -> DBResponse:
  identifier = _normalize_provider_identifier(args["provider_identifier"])
  sql = """
    SELECT TOP 1
      au.element_guid AS guid,
      au.element_soft_deleted_at
    FROM users_auth ua
    JOIN account_users au ON au.element_guid = ua.users_guid
    WHERE ua.element_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (identifier,))
  return DBResponse(payload=response.payload)


async def get_user_by_email(
  args: GetUserByEmailRequestPayload,
) -> DBResponse:
  email = args["email"]
  sql = """
    SELECT TOP 1
      element_guid AS guid
    FROM account_users
    WHERE element_email = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (email,))
  return DBResponse(payload=response.payload)


async def create_from_provider(
  args: CreateFromProviderRequestPayload,
) -> DBResponse:
  new_guid = str(uuid4())
  element_rotkey = ""
  element_rotkey_iat = datetime.now(timezone.utc)
  element_rotkey_exp = datetime.now(timezone.utc)
  provider = args["provider"]
  identifier = _normalize_provider_identifier(args["provider_identifier"])
  provider_email = args["provider_email"]
  provider_displayname = args["provider_displayname"]
  provider_profileimg = args.get("provider_profile_image", "")

  ap_recid = await _get_auth_provider_recid(provider)

  dup = await run_json_one(
    "SELECT users_guid FROM users_auth WHERE element_identifier = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (identifier,),
  )
  if dup.rows:
    existing_guid = dup.rows[0]["users_guid"]
    await run_exec(
      "UPDATE users_auth SET element_linked = 1, providers_recid = ? WHERE element_identifier = ?;",
      (ap_recid, identifier),
    )
    await run_exec(
      "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
      (ap_recid, existing_guid),
    )
    return await get_by_provider_identifier({
      "provider": provider,
      "provider_identifier": identifier,
    })

  async with transaction() as cur:
    await cur.execute(
      """
        INSERT INTO account_users (element_guid, element_email, element_display, providers_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
        VALUES (?, ?, ?, ?, ?, ?, ?);
      """,
      (new_guid, provider_email, provider_displayname, ap_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp),
    )
    await cur.execute(
      "INSERT INTO users_auth (users_guid, providers_recid, element_identifier, element_linked) VALUES (?, ?, ?, 1);",
      (new_guid, ap_recid, identifier),
    )
    await cur.execute(
      "INSERT INTO users_credits (users_guid, element_credits) VALUES (?, ?);",
      (new_guid, 50),
    )
    await cur.execute(
      "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
      (new_guid, provider_profileimg, ap_recid),
    )
    await cur.execute(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (new_guid, 1),
    )

  return await get_by_provider_identifier({
    "provider": provider,
    "provider_identifier": identifier,
  })


async def link_provider(
  args: LinkProviderRequestPayload,
) -> DBResponse:
  guid = _normalize_provider_identifier(args["guid"])
  provider = args["provider"]
  identifier = _normalize_provider_identifier(args["provider_identifier"])
  ap_recid = await _get_auth_provider_recid(provider)
  response = await run_exec(
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
    (guid, ap_recid, identifier),
  )
  return DBResponse(payload={"rowcount": response.rowcount})


async def unlink_provider(
  args: UnlinkProviderRequestPayload,
) -> DBResponse:
  guid = _normalize_provider_identifier(args["guid"])
  provider = args["provider"]
  new_recid = args.get("new_provider_recid")
  async with transaction() as cur:
    await cur.execute(
      "SELECT providers_recid FROM account_users WHERE element_guid = ?;",
      (guid,),
    )
    row = await cur.fetchone()
    current_recid = row[0] if row else None
    provider_recid = await _get_auth_provider_recid(provider, cursor=cur)
    await cur.execute(
      """
      UPDATE ua
      SET ua.element_linked = 0
      FROM users_auth ua
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      WHERE ua.users_guid = ? AND ap.element_name = ?;
      """,
      (guid, provider),
    )
    await cur.execute(
      "SELECT COUNT(*) AS cnt FROM users_auth WHERE users_guid = ? AND element_linked = 1;",
      (guid,),
    )
    row = await cur.fetchone()
    cnt = row[0] if row else 0
    if cnt == 0:
      await cur.execute(
        "UPDATE users_roles SET element_roles = 0 WHERE users_guid = ?;",
        (guid,),
      )
      await cur.execute(
        "UPDATE account_users SET providers_recid = NULL, element_display = '', element_email = '' WHERE element_guid = ?;",
        (guid,),
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
  return DBResponse(payload={"providers_remaining": cnt})


async def unlink_last_provider(
  args: UnlinkLastProviderRequestPayload,
) -> DBResponse:
  guid = args["guid"]
  provider = args["provider"]
  sql = "EXEC auth_unlink_last_provider @guid=?, @provider=?;"
  response = await run_exec(sql, (guid, provider))
  return DBResponse(payload={"rowcount": response.rowcount})


async def set_provider(
  args: SetProviderRequestPayload,
) -> DBResponse:
  guid = args["guid"]
  provider = args["provider"]
  ap_recid = await _get_auth_provider_recid(provider)
  response = await run_exec(
    "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
    (ap_recid, guid),
  )
  return DBResponse(payload={"rowcount": response.rowcount})


async def relink_provider(
  args: RelinkProviderRequestPayload,
) -> DBResponse:
  provider = args["provider"]
  if provider == "discord":
    identifier = _normalize_discord_identifier(args["provider_identifier"])
  else:
    identifier = _normalize_provider_identifier(args["provider_identifier"])

  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")

  if provider not in {"discord", "google", "microsoft"}:
    raise ValueError(f"Unsupported provider '{provider}' for relink")

  sql = "EXEC auth_oauth_relink @provider=?, @identifier=?, @email=?, @display=?, @image=?;"
  await run_exec(sql, (provider, identifier, email, display, img))
  return await get_by_provider_identifier({
    "provider": provider,
    "provider_identifier": identifier,
  })


async def soft_delete_account(
  args: SoftDeleteAccountRequestPayload,
) -> DBResponse:
  guid = _normalize_guid(args["guid"])
  sql = """
    UPDATE account_users
    SET element_soft_deleted_at = SYSDATETIMEOFFSET()
    WHERE element_guid = ?;
  """
  response = await run_exec(sql, (guid,))
  return DBResponse(payload={"rowcount": response.rowcount})

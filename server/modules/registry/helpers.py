"""Re-export registry request builders for use within modules."""

import logging
from collections.abc import Awaitable, Callable

from fastapi import HTTPException
from queryregistry.handler import dispatch_query_request
from queryregistry.models import DBRequest as QueryDBRequest, DBResponse as QueryDBResponse
from server.registry.account.cache import (
  count_rows_request,
  delete_cache_folder_request,
  delete_cache_item_request,
  list_cache_request,
  list_public_request,
  list_reported_request,
  replace_user_cache_request,
  set_reported_request,
  upsert_cache_item_request,
)
from server.registry.account.files import set_gallery_request
from server.registry.account.oauth import (
  relink_discord_request,
  relink_google_request,
  relink_microsoft_request,
)
from server.registry.finance.credits import set_credits_request
from server.registry.account.profile import (
  get_profile_request as _profile_get_profile_request,
  get_roles_request,
  set_display_request,
  set_optin_request,
  set_profile_image_request,
  update_if_unedited_request,
)
from server.registry.account.providers import (
  create_from_provider_request,
  get_any_by_provider_identifier_request,
  get_by_provider_identifier_request,
  get_user_by_email_request,
  link_provider_request,
  set_provider_request,
  unlink_last_provider_request,
  unlink_provider_request,
)
from server.registry.account.public import get_public_files_request
from server.registry.account.session import (
  create_session_request,
  get_rotkey_request,
  revoke_device_token_request,
  revoke_provider_tokens_request,
  set_rotkey_request,
  update_device_token_request,
  update_session_request,
)
from server.registry.system.config import (
  delete_config_request,
  get_config_request,
  get_configs_request,
  upsert_config_request,
)
from server.registry.system.conversations import (
  find_recent_request,
  insert_conversation_request,
  list_by_time_request,
  update_output_request,
)
from server.registry.system.models import list_models_request
from server.registry.system.personas import (
  delete_persona_request,
  get_persona_by_name_request,
  list_personas_request,
  upsert_persona_request,
)
from server.registry.system.public_users import (
  get_profile_request as get_public_user_profile_request,
  get_published_files_request,
)
from server.registry.system.routes import (
  delete_route_request,
  get_routes_request,
  upsert_route_request,
)
from server.registry.system.roles import (
  add_role_member_request,
  get_role_members_request,
  get_role_non_members_request,
  remove_role_member_request,
)
from server.registry.system.roles.model import (
  DeleteRoleParams,
  ModifyRoleMemberParams,
  RoleScopeParams,
  UpsertRoleParams,
)
from server.registry.system.public_vars import (
  get_hostname_request,
  get_repo_request,
  get_version_request,
)

def get_identity_security_profile_request(
  *,
  guid: str | None = None,
  access_token: str | None = None,
  provider: str | None = None,
  provider_identifier: str | None = None,
  discord_id: str | None = None,
) -> QueryDBRequest:
  params: dict[str, object] = {}
  if guid is not None:
    params["guid"] = guid
  if access_token is not None:
    params["access_token"] = access_token
  if provider is not None:
    params["provider"] = provider
  if provider_identifier is not None:
    params["provider_identifier"] = provider_identifier
  if discord_id is not None:
    params["discord_id"] = discord_id
  return QueryDBRequest(op="db:identity:accounts:read:1", payload=params)


def identity_account_exists_request(user_guid: str) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:identity:accounts:exists:1",
    payload={"user_guid": user_guid},
  )


def list_role_memberships_request(params: RoleScopeParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:identity:role_memberships:list:1",
    payload=params.model_dump(),
  )


def list_role_non_memberships_request(params: RoleScopeParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:identity:role_memberships:list_non_members:1",
    payload=params.model_dump(),
  )


def create_role_membership_request(params: ModifyRoleMemberParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:identity:role_memberships:create:1",
    payload=params.model_dump(),
  )


def delete_role_membership_request(params: ModifyRoleMemberParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:identity:role_memberships:delete:1",
    payload=params.model_dump(),
  )


def list_system_roles_request() -> QueryDBRequest:
  return QueryDBRequest(op="db:system:roles:list:1", payload={})


def get_home_links_request() -> QueryDBRequest:
  return QueryDBRequest(op="db:system:links:get_home_links:1", payload={})


def get_navbar_routes_request(role_mask: int | None = None) -> QueryDBRequest:
  payload: dict[str, object] = {}
  if role_mask is not None:
    payload["role_mask"] = role_mask
  return QueryDBRequest(op="db:system:links:get_navbar_routes:1", payload=payload)


def create_system_role_request(params: UpsertRoleParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:system:roles:create:1",
    payload=params.model_dump(),
  )


def update_system_role_request(params: UpsertRoleParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:system:roles:update:1",
    payload=params.model_dump(),
  )


def delete_system_role_request(params: DeleteRoleParams) -> QueryDBRequest:
  return QueryDBRequest(
    op="db:system:roles:delete:1",
    payload=params.model_dump(),
  )


def _log_registry_fallback(op: str, provider: str, reason: str) -> None:
  registry_logger = logging.getLogger("server.registry")
  registry_logger.warning(
    "Registry handler fallback triggered",
    extra={
      "db_op": op,
      "db_provider": provider,
      "db_fallback_reason": reason,
    },
  )
  metrics_logger = logging.getLogger("metrics.registry")
  metrics_logger.info(
    "db_registry_fallback",
    extra={
      "db_op": op,
      "db_provider": provider,
      "db_fallback_reason": reason,
    },
  )


async def dispatch_query_request_with_fallback(
  request: QueryDBRequest,
  *,
  provider: str,
  fallback: Callable[[], Awaitable[QueryDBResponse]] | None = None,
) -> QueryDBResponse:
  try:
    response = await dispatch_query_request(request, provider=provider)
  except (KeyError, HTTPException) as exc:
    if isinstance(exc, HTTPException) and exc.status_code != 404:
      raise
    _log_registry_fallback(request.op, provider, "missing_handler")
    if fallback is None:
      raise
    return await fallback()
  logging.getLogger("server.registry").info(
    "Registry handler resolved",
    extra={"db_op": request.op, "db_provider": provider},
  )
  return response


get_profile_request = _profile_get_profile_request

__all__ = sorted([
  "add_role_member_request",
  "count_rows_request",
  "create_role_membership_request",
  "create_from_provider_request",
  "create_session_request",
  "delete_cache_folder_request",
  "delete_cache_item_request",
  "delete_config_request",
  "delete_role_membership_request",
  "delete_persona_request",
  "delete_route_request",
  "delete_system_role_request",
  "dispatch_query_request_with_fallback",
  "find_recent_request",
  "get_any_by_provider_identifier_request",
  "get_by_provider_identifier_request",
  "get_config_request",
  "get_configs_request",
  "get_home_links_request",
  "get_hostname_request",
  "get_navbar_routes_request",
  "get_persona_by_name_request",
  "get_profile_request",
  "get_public_files_request",
  "get_public_user_profile_request",
  "get_published_files_request",
  "get_repo_request",
  "get_role_members_request",
  "get_role_non_members_request",
  "get_roles_request",
  "get_rotkey_request",
  "get_routes_request",
  "get_identity_security_profile_request",
  "get_user_by_email_request",
  "get_version_request",
  "identity_account_exists_request",
  "insert_conversation_request",
  "link_provider_request",
  "list_by_time_request",
  "list_cache_request",
  "list_models_request",
  "list_role_memberships_request",
  "list_role_non_memberships_request",
  "list_personas_request",
  "list_public_request",
  "list_reported_request",
  "list_system_roles_request",
  "relink_discord_request",
  "relink_google_request",
  "relink_microsoft_request",
  "remove_role_member_request",
  "replace_user_cache_request",
  "revoke_device_token_request",
  "revoke_provider_tokens_request",
  "create_system_role_request",
  "set_credits_request",
  "set_display_request",
  "set_gallery_request",
  "set_optin_request",
  "set_profile_image_request",
  "set_provider_request",
  "set_reported_request",
  "set_rotkey_request",
  "unlink_last_provider_request",
  "unlink_provider_request",
  "update_device_token_request",
  "update_if_unedited_request",
  "update_output_request",
  "update_session_request",
  "update_system_role_request",
  "upsert_cache_item_request",
  "upsert_config_request",
  "upsert_persona_request",
  "upsert_route_request",
])

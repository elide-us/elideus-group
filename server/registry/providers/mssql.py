"""MSSQL provider callable bindings."""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Mapping
from typing import Any

from server.modules.providers import DBResult
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers.database.mssql_provider.db_helpers import Operation
from server.registry.types import DBRequest, DBResponse

from . import ProviderCallable, ProviderQueryMap

__all__ = [
  "PROVIDER_QUERIES",
]


async def _coerce_response(spec: Any) -> DBResponse:
  if isinstance(spec, DBResponse):
    return spec
  if inspect.isawaitable(spec):
    return await _coerce_response(await spec)
  if isinstance(spec, Operation):
    result = await mssql_provider.execute_operation(spec)
    return DBResponse.from_result(result)
  if isinstance(spec, DBResult):
    return DBResponse.from_result(spec)
  if isinstance(spec, Mapping):
    validator = getattr(DBResult, "model_validate", None)
    if callable(validator):
      return DBResponse.from_result(validator(spec))
    return DBResponse.from_result(DBResult(**spec))
  if spec is None:
    return DBResponse()
  raise TypeError(f"Unsupported provider specification result: {type(spec)!r}")


def _wrap(fn: Any) -> ProviderCallable:
  async def _executor(request: DBRequest) -> DBResponse:
    spec = fn(request.params)
    return await _coerce_response(spec)
  return _executor


def _wrap_lazy(module_path: str, attr_name: str) -> ProviderCallable:
  def _invoke(params: dict[str, Any]) -> Any:
    module = importlib.import_module(module_path)
    fn = getattr(module, attr_name)
    return fn(params)
  return _wrap(_invoke)


_PROVIDER_SPECS: dict[str, tuple[str, str]] = {
  "security.accounts.get_security_profile": ("server.registry.security.accounts.mssql", "get_security_profile_v1"),
  "security.accounts.account_exists": ("server.registry.security.accounts.mssql", "account_exists_v1"),
  "assistant.conversations.find_recent": ("server.registry.assistant.conversations.mssql", "find_recent_v1"),
  "assistant.conversations.insert": ("server.registry.assistant.conversations.mssql", "insert_conversation_v1"),
  "assistant.conversations.list_by_time": ("server.registry.assistant.conversations.mssql", "list_by_time_v1"),
  "assistant.conversations.list_recent": ("server.registry.assistant.conversations.mssql", "list_recent_v1"),
  "assistant.conversations.update_output": ("server.registry.assistant.conversations.mssql", "update_output_v1"),
  "assistant.models.get_by_name": ("server.registry.assistant.models.mssql", "get_by_name_v1"),
  "assistant.models.list": ("server.registry.assistant.models.mssql", "list_models_v1"),
  "assistant.personas.delete": ("server.registry.assistant.personas.mssql", "delete_persona_v1"),
  "assistant.personas.get_by_name": ("server.registry.assistant.personas.mssql", "get_by_name_v1"),
  "assistant.personas.list": ("server.registry.assistant.personas.mssql", "list_personas_v1"),
  "assistant.personas.upsert": ("server.registry.assistant.personas.mssql", "upsert_persona_v1"),
  "security.oauth.relink_discord": ("server.registry.security.oauth.mssql", "relink_discord_v1"),
  "security.oauth.relink_google": ("server.registry.security.oauth.mssql", "relink_google_v1"),
  "security.oauth.relink_microsoft": ("server.registry.security.oauth.mssql", "relink_microsoft_v1"),
  "security.identities.unlink_last_provider": ("server.registry.security.identities.mssql", "unlink_last_provider_v1"),
  "security.identities.create_from_provider": ("server.registry.security.identities.mssql", "create_from_provider_v1"),
  "security.identities.get_any_by_provider_identifier": ("server.registry.security.identities.mssql", "get_any_by_provider_identifier_v1"),
  "security.identities.get_by_provider_identifier": ("server.registry.security.identities.mssql", "get_by_provider_identifier_v1"),
  "security.identities.get_user_by_email": ("server.registry.security.identities.mssql", "get_user_by_email_v1"),
  "security.identities.link_provider": ("server.registry.security.identities.mssql", "link_provider_v1"),
  "security.identities.set_provider": ("server.registry.security.identities.mssql", "set_provider_v1"),
  "security.identities.soft_delete_account": ("server.registry.security.identities.mssql", "soft_delete_account_v1"),
  "security.identities.unlink_provider": ("server.registry.security.identities.mssql", "unlink_provider_v1"),
  "security.sessions.create_session": ("server.registry.security.sessions.mssql", "create_session_v1"),
  "security.sessions.revoke_all_device_tokens": ("server.registry.security.sessions.mssql", "revoke_all_device_tokens_v1"),
  "security.sessions.revoke_device_token": ("server.registry.security.sessions.mssql", "revoke_device_token_v1"),
  "security.sessions.revoke_provider_tokens": ("server.registry.security.sessions.mssql", "revoke_provider_tokens_v1"),
  "security.sessions.update_device_token": ("server.registry.security.sessions.mssql", "update_device_token_v1"),
  "security.sessions.update_session": ("server.registry.security.sessions.mssql", "update_session_v1"),
  "security.sessions.set_rotkey": ("server.registry.security.sessions.mssql", "set_rotkey_v1"),
  "content.cache.count_rows": ("server.registry.content.cache.mssql", "count_rows_v1"),
  "content.cache.delete": ("server.registry.content.cache.mssql", "delete_v1"),
  "content.cache.delete_folder": ("server.registry.content.cache.mssql", "delete_folder_v1"),
  "content.cache.list": ("server.registry.content.cache.mssql", "list_v1"),
  "content.cache.replace_user": ("server.registry.content.cache.mssql", "replace_user_v1"),
  "content.cache.set_public": ("server.registry.content.cache.mssql", "set_public_v1"),
  "content.cache.set_reported": ("server.registry.content.cache.mssql", "set_reported_v1"),
  "content.cache.upsert": ("server.registry.content.cache.mssql", "upsert_v1"),
  "content.files.set_gallery": ("server.registry.content.files.mssql", "set_gallery_v1"),
  "content.public.get_public_files": ("server.registry.content.public.mssql", "get_public_files_v1"),
  "content.public.list_public": ("server.registry.content.public.mssql", "list_public_v1"),
  "content.public.list_reported": ("server.registry.content.public.mssql", "list_reported_v1"),
  "public.links.get_home_links": ("server.registry.public.links.mssql", "get_home_links_v1"),
  "public.links.get_navbar_routes": ("server.registry.public.links.mssql", "get_navbar_routes_v1"),
  "public.users.get_profile": ("server.registry.public.users.mssql", "get_profile_v1"),
  "public.users.get_published_files": ("server.registry.public.users.mssql", "get_published_files_v1"),
  "public.vars.get_hostname": ("server.registry.public.vars.mssql", "get_hostname_v1"),
  "public.vars.get_repo": ("server.registry.public.vars.mssql", "get_repo_v1"),
  "public.vars.get_version": ("server.registry.public.vars.mssql", "get_version_v1"),
  "account.users.set_credits": ("server.registry.account.users.mssql", "set_credits_v1"),
  "support.users.set_credits": ("server.registry.support.users.mssql", "set_credits_v1"),
  "system.config.delete_config": ("server.registry.system.config.mssql", "delete_config_v1"),
  "system.config.get_config": ("server.registry.system.config.mssql", "get_config_v1"),
  "system.config.get_configs": ("server.registry.system.config.mssql", "get_configs_v1"),
  "system.config.upsert_config": ("server.registry.system.config.mssql", "upsert_config_v1"),
  "system.roles.add_role_member": ("server.registry.system.roles.mssql", "add_role_member_v1"),
  "system.roles.delete_role": ("server.registry.system.roles.mssql", "delete_role_v1"),
  "system.roles.get_role_members": ("server.registry.system.roles.mssql", "get_role_members_v1"),
  "system.roles.get_role_non_members": ("server.registry.system.roles.mssql", "get_role_non_members_v1"),
  "system.roles.list": ("server.registry.system.roles.mssql", "list_roles_v1"),
  "system.roles.remove_role_member": ("server.registry.system.roles.mssql", "remove_role_member_v1"),
  "system.roles.upsert_role": ("server.registry.system.roles.mssql", "upsert_role_v1"),
  "system.routes.delete_route": ("server.registry.system.routes.mssql", "delete_route_v1"),
  "system.routes.get_routes": ("server.registry.system.routes.mssql", "get_routes_v1"),
  "system.routes.upsert_route": ("server.registry.system.routes.mssql", "upsert_route_v1"),
  "users.profile.get_profile": ("server.registry.users.profile.mssql", "get_profile_v1"),
  "users.profile.set_display": ("server.registry.users.profile.mssql", "set_display_v1"),
  "users.profile.set_optin": ("server.registry.users.profile.mssql", "set_optin_v1"),
  "users.profile.set_profile_image": ("server.registry.users.profile.mssql", "set_profile_image_v1"),
  "users.profile.set_roles": ("server.registry.users.profile.mssql", "set_roles_v1"),
  "users.profile.update_if_unedited": ("server.registry.users.profile.mssql", "update_if_unedited_v1"),
}


PROVIDER_QUERIES: ProviderQueryMap = {
  key: {1: _wrap_lazy(module, attr)}
  for key, (module, attr) in _PROVIDER_SPECS.items()
}

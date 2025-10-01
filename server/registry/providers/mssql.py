"""MSSQL provider callable bindings."""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Mapping
from typing import Any

from server.modules.providers import DBResult
from server.modules.providers.database.mssql_provider.db_helpers import Operation, execute_operation
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
    result = await execute_operation(spec)
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
  "accounts.security.get_security_profile": ("server.registry.accounts.security.mssql", "get_security_profile_v1"),
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
  "auth.discord.oauth_relink": ("server.registry.auth.discord.mssql", "oauth_relink_v1"),
  "auth.google.oauth_relink": ("server.registry.auth.google.mssql", "oauth_relink_v1"),
  "auth.microsoft.oauth_relink": ("server.registry.auth.microsoft.mssql", "oauth_relink_v1"),
  "auth.providers.unlink_last_provider": ("server.registry.auth.providers.mssql", "unlink_last_provider_v1"),
  "auth.session.create_session": ("server.registry.auth.session.mssql", "create_session_v1"),
  "auth.session.revoke_all_device_tokens": ("server.registry.auth.session.mssql", "revoke_all_device_tokens_v1"),
  "auth.session.revoke_device_token": ("server.registry.auth.session.mssql", "revoke_device_token_v1"),
  "auth.session.revoke_provider_tokens": ("server.registry.auth.session.mssql", "revoke_provider_tokens_v1"),
  "auth.session.update_device_token": ("server.registry.auth.session.mssql", "update_device_token_v1"),
  "auth.session.update_session": ("server.registry.auth.session.mssql", "update_session_v1"),
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
  "public.gallery.get_public_files": ("server.registry.content.public.mssql", "get_public_files_v1"),
  "public.links.get_home_links": ("server.registry.public.links.mssql", "get_home_links_v1"),
  "public.links.get_navbar_routes": ("server.registry.public.links.mssql", "get_navbar_routes_v1"),
  "public.users.get_profile": ("server.registry.public.users.mssql", "get_profile_v1"),
  "public.users.get_published_files": ("server.registry.public.users.mssql", "get_published_files_v1"),
  "public.vars.get_hostname": ("server.registry.public.vars.mssql", "get_hostname_v1"),
  "public.vars.get_repo": ("server.registry.public.vars.mssql", "get_repo_v1"),
  "public.vars.get_version": ("server.registry.public.vars.mssql", "get_version_v1"),
  "security.roles.add_role_member": ("server.registry.security.roles.mssql", "add_role_member_v1"),
  "security.roles.delete_role": ("server.registry.security.roles.mssql", "delete_role_v1"),
  "security.roles.get_role_members": ("server.registry.security.roles.mssql", "get_role_members_v1"),
  "security.roles.get_role_non_members": ("server.registry.security.roles.mssql", "get_role_non_members_v1"),
  "security.roles.remove_role_member": ("server.registry.security.roles.mssql", "remove_role_member_v1"),
  "security.roles.upsert_role": ("server.registry.security.roles.mssql", "upsert_role_v1"),
  "service.routes.delete_route": ("server.registry.service.routes.mssql", "delete_route_v1"),
  "service.routes.get_routes": ("server.registry.service.routes.mssql", "get_routes_v1"),
  "service.routes.upsert_route": ("server.registry.service.routes.mssql", "upsert_route_v1"),
  "support.users.set_credits": ("server.registry.support.users.mssql", "set_credits_v1"),
  "system.config.delete_config": ("server.registry.system.config.mssql", "delete_config_v1"),
  "system.config.get_config": ("server.registry.system.config.mssql", "get_config_v1"),
  "system.config.get_configs": ("server.registry.system.config.mssql", "get_configs_v1"),
  "system.config.upsert_config": ("server.registry.system.config.mssql", "upsert_config_v1"),
  "system.roles.list": ("server.registry.system.roles.mssql", "list_roles_v1"),
  "users.account.exists": ("server.registry.users.account.mssql", "account_exists_v1"),
  "users.profile.get_profile": ("server.registry.users.profile.mssql", "get_profile_v1"),
  "users.profile.set_display": ("server.registry.users.profile.mssql", "set_display_v1"),
  "users.profile.set_optin": ("server.registry.users.profile.mssql", "set_optin_v1"),
  "users.profile.set_profile_image": ("server.registry.users.profile.mssql", "set_profile_image_v1"),
  "users.profile.set_roles": ("server.registry.users.profile.mssql", "set_roles_v1"),
  "users.profile.update_if_unedited": ("server.registry.users.profile.mssql", "update_if_unedited_v1"),
  "users.providers.create_from_provider": ("server.registry.users.providers.mssql", "create_from_provider_v1"),
  "users.providers.get_any_by_provider_identifier": ("server.registry.users.providers.mssql", "get_any_by_provider_identifier_v1"),
  "users.providers.get_by_provider_identifier": ("server.registry.users.providers.mssql", "get_by_provider_identifier_v1"),
  "users.providers.get_user_by_email": ("server.registry.users.providers.mssql", "get_user_by_email_v1"),
  "users.providers.link_provider": ("server.registry.users.providers.mssql", "link_provider_v1"),
  "users.providers.set_provider": ("server.registry.users.providers.mssql", "set_provider_v1"),
  "users.providers.soft_delete_account": ("server.registry.users.providers.mssql", "soft_delete_account_v1"),
  "users.providers.unlink_provider": ("server.registry.users.providers.mssql", "unlink_provider_v1"),
  "users.session.set_rotkey": ("server.registry.users.session.mssql", "set_rotkey_v1"),
}


PROVIDER_QUERIES: ProviderQueryMap = {
  key: {1: _wrap_lazy(module, attr)}
  for key, (module, attr) in _PROVIDER_SPECS.items()
}

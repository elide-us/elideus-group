"""Seed reflection_rpc_* tables from the /rpc namespace source code."""

from __future__ import annotations

import argparse
import ast
import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any, Union, get_args, get_origin

import pyodbc
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT, load_module

load_dotenv(os.path.join(REPO_ROOT, ".env"))

RPC_ROOT = Path(REPO_ROOT) / "rpc"
APP_VERSION = "0.10.3.0"

DOMAIN_ROLES = {
  "support": "ROLE_SUPPORT",
  "auth": None,
  "moderation": "ROLE_MODERATOR",
  "public": None,
  "service": "ROLE_SERVICE_ADMIN",
  "storage": "ROLE_STORAGE",
  "system": "ROLE_SYSTEM_ADMIN",
  "users": "ROLE_REGISTERED",
  "account": "ROLE_ACCOUNT_ADMIN",
  "discord": "ROLE_DISCORD_ADMIN",
  "finance": "ROLE_FINANCE_ADMIN",
}

EDT_MAP = {
  str: 8,
  int: 1,
  bool: 5,
}

MODULE_ATTR_MAP: dict[tuple[str, str], str] = {
  # support domain — delegates to account services
  ("support", "users"): "user_admin",
  ("support", "roles"): "role_admin",
  # auth domain
  ("auth", "microsoft"): "oauth",
  ("auth", "google"): "oauth",
  ("auth", "discord"): "oauth",
  ("auth", "providers"): "oauth",
  ("auth", "session"): "session",
  # moderation
  ("moderation", "content"): "moderation",
  # public domain
  ("public", "links"): "public_links",
  ("public", "vars"): "public_vars",
  ("public", "users"): "public_users",
  ("public", "gallery"): "public_gallery",
  # service domain
  ("service", "roles"): "role_admin",
  ("service", "routes"): "service_routes",
  ("service", "reflection"): "db",
  ("service", "renewals"): "db",
  ("service", "payment_requests"): "db",
  # storage
  ("storage", "files"): "storage",
  # system domain
  ("system", "batch_jobs"): "batch_job",
  ("system", "config"): "system_config",
  ("system", "conversations"): "db",
  ("system", "models"): "db",
  ("system", "roles"): "role_admin",
  ("system", "storage"): "storage",
  ("system", "tasks"): "async_task",
  # users domain
  ("users", "profile"): "profile",
  ("users", "products"): "finance",
  ("users", "providers"): "oauth",
  # account domain
  ("account", "role"): "role_admin",
  ("account", "user"): "user_admin",
  # discord domain
  ("discord", "bsky"): "bsky",
  ("discord", "chat"): "discord_chat",
  ("discord", "command"): "auth",
  ("discord", "guilds"): "db",
  ("discord", "personas"): "openai",
  # finance domain — all subdomains use finance module
  ("finance", "accounts"): "finance",
  ("finance", "credit_lots"): "finance",
  ("finance", "dimensions"): "finance",
  ("finance", "journals"): "finance",
  ("finance", "ledgers"): "finance",
  ("finance", "numbers"): "finance",
  ("finance", "product_journal_config"): "finance",
  ("finance", "products"): "finance",
  ("finance", "pipeline_config"): "finance",
  ("finance", "periods"): "finance",
  ("finance", "reporting"): "finance",
  ("finance", "staging"): "finance",
  ("finance", "staging_account_map"): "finance",
  ("finance", "staging_purge_log"): "finance",
  ("finance", "vendors"): "finance",
}

METHOD_NAME_OVERRIDES: dict[tuple[str, str, str], str] = {
  # storage.files — AST matches reindex() instead of the business method
  ("storage", "files", "get_files"): "list_files_by_user",
  ("storage", "files", "upload_files"): "upload_files",
  ("storage", "files", "delete_files"): "delete_files",
  ("storage", "files", "set_gallery"): "set_gallery",
  ("storage", "files", "create_folder"): "create_folder",
  ("storage", "files", "move_file"): "move_file",
  ("storage", "files", "rename_file"): "rename_file",
  ("storage", "files", "get_link"): "get_file_link",
  ("storage", "files", "get_metadata"): "get_file_metadata",
  ("storage", "files", "get_folder_files"): "list_folder",
  ("storage", "files", "delete_folder"): "delete_folder",
  ("storage", "files", "create_user_folder"): "create_user_folder",
  ("storage", "files", "get_usage"): "get_usage",
  ("storage", "files", "get_public_files"): "list_public_files",
  ("storage", "files", "get_moderation_files"): "list_flagged_for_moderation",
  ("storage", "files", "report_file"): "report_file",
  # system.storage
  ("system", "storage", "get_stats"): "get_storage_stats",
  # service.routes — AST resolves internal model conversion
  ("service", "routes", "get_routes"): "get_routes",
  ("service", "routes", "upsert_route"): "upsert_route",
  ("service", "routes", "delete_route"): "delete_route",
  # support.users — delegates to account.user services
  ("support", "users", "get_displayname"): "get_displayname",
  ("support", "users", "get_credits"): "get_credits",
  ("support", "users", "set_credits"): "set_credits",
  ("support", "users", "reset_display"): "reset_display",
  # users.products — AST matched get_user_roles_mask instead
  ("users", "products", "list"): "list_products",
  ("users", "products", "purchase"): "purchase_product",
  # auth.microsoft
  ("auth", "microsoft", "oauth_login"): "login_provider",
  ("auth", "microsoft", "oauth_relink"): "relink_provider",
  # auth.google
  ("auth", "google", "oauth_login"): "login_provider",
  ("auth", "google", "oauth_relink"): "relink_provider",
  # auth.discord
  ("auth", "discord", "oauth_login"): "login_provider",
  ("auth", "discord", "oauth_relink"): "relink_provider",
  # auth.providers
  ("auth", "providers", "unlink_last_provider"): "unlink_last_provider_record",
  # auth.session
  ("auth", "session", "get_token"): "issue_token",
  ("auth", "session", "refresh_token"): "refresh_token",
  ("auth", "session", "invalidate_token"): "invalidate_token",
  ("auth", "session", "logout_device"): "logout_device",
  ("auth", "session", "get_session"): "get_session",
  # discord.bsky
  ("discord", "bsky", "post"): "post_message",
  # discord.chat
  ("discord", "chat", "summarize_channel"): "deliver_summary",
  ("discord", "chat", "persona_response"): "persona_response",
  ("discord", "chat", "persona_command"): "persona_command",
  ("discord", "chat", "get_persona"): "get_persona",
  ("discord", "chat", "get_conversation_history"): "get_conversation_history",
  ("discord", "chat", "get_channel_history"): "get_channel_history",
  ("discord", "chat", "insert_conversation_input"): "insert_conversation_input",
  ("discord", "chat", "generate_persona_response"): "generate_persona_response",
  ("discord", "chat", "deliver_persona_response"): "deliver_persona_response",
  # discord.command
  ("discord", "command", "get_roles"): "get_discord_user_security",
  ("discord", "command", "register"): "register_discord_user",
  ("discord", "command", "get_credits"): "get_credits",
  ("discord", "command", "get_guild_credits"): "get_guild_credits",
  # discord.guilds
  ("discord", "guilds", "list_guilds"): "list_guilds",
  ("discord", "guilds", "get_guild"): "get_guild",
  ("discord", "guilds", "update_credits"): "update_guild_credits",
  ("discord", "guilds", "sync_guilds"): "sync_guilds",
  # discord.personas
  ("discord", "personas", "get_personas"): "list_personas",
  ("discord", "personas", "get_models"): "list_models",
  ("discord", "personas", "upsert_persona"): "upsert_persona",
  ("discord", "personas", "delete_persona"): "delete_persona",
  # moderation
  ("moderation", "content", "review_content"): "review_content",
  # public domain
  ("public", "links", "get_home_links"): "get_home_links",
  ("public", "links", "get_navbar_routes"): "get_navbar_routes",
  ("public", "vars", "get_versions"): "get_versions",
  ("public", "users", "get_profile"): "get_profile",
  ("public", "users", "get_published_files"): "get_published_files",
  ("public", "gallery", "get_public_files"): "list_public_files",
  # service domain
  ("service", "roles", "get_roles"): "list_roles",
  ("service", "roles", "upsert_role"): "upsert_role",
  ("service", "roles", "delete_role"): "delete_role",
  ("service", "renewals", "list"): "list_renewals",
  ("service", "renewals", "get"): "get_renewal",
  ("service", "renewals", "upsert"): "upsert_renewal",
  ("service", "renewals", "delete"): "delete_renewal",
  ("service", "payment_requests", "create"): "create_payment_request",
  ("service", "reflection", "list_tables"): "list_tables",
  ("service", "reflection", "describe_table"): "describe_table",
  ("service", "reflection", "list_views"): "list_views",
  ("service", "reflection", "get_full_schema"): "get_full_schema",
  ("service", "reflection", "get_schema_version"): "get_schema_version",
  ("service", "reflection", "dump_table"): "dump_table",
  ("service", "reflection", "query_info_schema"): "query_info_schema",
  ("service", "reflection", "list_domains"): "list_domains",
  ("service", "reflection", "list_rpc_endpoints"): "list_rpc_endpoints",
  # system domain
  ("system", "batch_jobs", "list"): "list_jobs",
  ("system", "batch_jobs", "get"): "get_job",
  ("system", "batch_jobs", "upsert"): "upsert_job",
  ("system", "batch_jobs", "delete"): "delete_job",
  ("system", "batch_jobs", "list_history"): "list_history",
  ("system", "batch_jobs", "run_now"): "run_now",
  ("system", "config", "get_configs"): "get_configs",
  ("system", "config", "upsert_config"): "upsert_config",
  ("system", "config", "delete_config"): "delete_config",
  ("system", "conversations", "list_conversations"): "list_conversations",
  ("system", "conversations", "get_stats"): "get_stats",
  ("system", "conversations", "view_thread"): "view_thread",
  ("system", "conversations", "delete_thread"): "delete_thread",
  ("system", "conversations", "delete_before"): "delete_before",
  ("system", "models", "get_models"): "get_models",
  ("system", "models", "upsert_model"): "upsert_model",
  ("system", "models", "delete_model"): "delete_model",
  ("system", "roles", "get_roles"): "list_roles",
  ("system", "roles", "upsert_role"): "upsert_role",
  ("system", "roles", "delete_role"): "delete_role",
  ("system", "storage", "get_stats"): "get_storage_stats",
  ("system", "tasks", "list"): "list_tasks",
  ("system", "tasks", "get"): "get_task",
  ("system", "tasks", "submit"): "submit_task",
  ("system", "tasks", "cancel"): "cancel_task",
  ("system", "tasks", "retry"): "retry_task",
  ("system", "tasks", "events"): "list_task_events",
  # users domain
  ("users", "profile", "get_profile"): "get_profile",
  ("users", "profile", "set_display"): "set_display",
  ("users", "profile", "set_optin"): "set_optin",
  ("users", "profile", "get_roles"): "get_roles",
  ("users", "profile", "set_profile_image"): "set_profile_image",
  ("users", "providers", "set_provider"): "set_user_default_provider",
  ("users", "providers", "link_provider"): "link_user_provider",
  ("users", "providers", "unlink_provider"): "unlink_user_provider",
  ("users", "providers", "get_by_provider_identifier"): "get_user_by_provider_identifier",
  ("users", "providers", "create_from_provider"): "create_user_from_provider",
  # account domain
  ("account", "role", "get_roles"): "list_roles",
  ("account", "role", "get_all_role_members"): "get_all_role_members",
  ("account", "role", "get_role_members"): "get_role_members",
  ("account", "role", "add_role_member"): "add_role_member",
  ("account", "role", "remove_role_member"): "remove_role_member",
  ("account", "role", "upsert_role"): "upsert_role",
  ("account", "role", "delete_role"): "delete_role",
  ("account", "user", "get_displayname"): "get_displayname",
  ("account", "user", "get_credits"): "get_credits",
  ("account", "user", "set_credits"): "set_credits",
  ("account", "user", "reset_display"): "reset_display",
  ("account", "user", "create_folder"): "create_user_folder",
}

REQUEST_MODEL_OVERRIDES: dict[tuple[str, str, str], str] = {
  ("finance", "reporting", "trial_balance"): "TrialBalanceFilter1",
  ("finance", "reporting", "journal_summary"): "JournalSummaryFilter1",
  ("finance", "reporting", "period_status"): "PeriodStatusFilter1",
  ("finance", "reporting", "credit_lot_summary"): "CreditLotSummaryFilter1",
}


def parse_dict_keys(path: Path, dict_name: str) -> list[str]:
  tree = ast.parse(path.read_text(), filename=str(path))
  for node in tree.body:
    value = None
    if isinstance(node, ast.Assign):
      targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
      if dict_name in targets:
        value = node.value
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
      if node.target.id == dict_name:
        value = node.value
    if isinstance(value, ast.Dict):
      keys: list[str] = []
      for key in value.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
          keys.append(key.value)
      return keys
  return []


def parse_dispatchers(path: Path) -> list[dict[str, Any]]:
  tree = ast.parse(path.read_text(), filename=str(path))
  operations: list[dict[str, Any]] = []
  for node in tree.body:
    value = None
    if isinstance(node, ast.Assign):
      targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
      if "DISPATCHERS" in targets:
        value = node.value
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
      if node.target.id == "DISPATCHERS":
        value = node.value
    if isinstance(value, ast.Dict):
      for key, val in zip(value.keys, value.values):
        if not isinstance(key, ast.Tuple) or len(key.elts) != 2:
          continue
        left, right = key.elts
        if not isinstance(left, ast.Constant) or not isinstance(right, ast.Constant):
          continue
        if not isinstance(left.value, str):
          continue
        function_name = val.id if isinstance(val, ast.Name) else None
        operations.append(
          {
            "op": left.value,
            "version": int(right.value),
            "service_function": function_name,
          }
        )
      return operations
  return operations


def discover_domains() -> list[str]:
  return parse_dict_keys(RPC_ROOT / "__init__.py", "HANDLERS")


def discover_subdomains(domains: list[str]) -> list[tuple[str, str]]:
  rows: list[tuple[str, str]] = []
  for domain in domains:
    init_file = RPC_ROOT / domain / "__init__.py"
    for subdomain in parse_dict_keys(init_file, "HANDLERS"):
      rows.append((domain, subdomain))
  return rows


def resolve_alias_name(name: str, alias_map: dict[str, str]) -> str:
  resolved = name
  while resolved in alias_map:
    resolved = alias_map[resolved]
  return resolved


def discover_models() -> tuple[
  list[dict[str, Any]],
  dict[str, int],
  dict[str, type[BaseModel]],
  dict[str, str],
]:
  model_rows: list[dict[str, Any]] = []
  model_map: dict[str, int] = {}
  model_classes: dict[str, type[BaseModel]] = {}
  alias_map: dict[str, str] = {}

  recid = 1
  for models_file in sorted(RPC_ROOT.glob("**/models.py")):
    module = load_module(str(models_file))
    rel = models_file.relative_to(RPC_ROOT)
    parts = rel.parts
    domain = parts[0] if len(parts) > 1 else ""
    subdomain = parts[1] if len(parts) > 2 else ""

    for name, obj in inspect.getmembers(module, inspect.isclass):
      if not issubclass(obj, BaseModel) or obj is BaseModel:
        continue
      if name in {"RPCRequest", "RPCResponse"}:
        continue
      if obj.__module__ != module.__name__:
        continue
      if name in model_map:
        continue

      match = re.search(r"(\d+)$", name)
      version = int(match.group(1)) if match else 1
      model_rows.append(
        {
          "recid": recid,
          "element_name": name,
          "element_domain": domain,
          "element_subdomain": subdomain,
          "element_version": version,
          "parent_name": None,
          "is_alias": False,
          "flatten_fields": False,
          "model_class": obj,
        }
      )
      model_map[name] = recid
      model_classes[name] = obj
      recid += 1

  for row in model_rows:
    cls = row["model_class"]
    for base in cls.__bases__:
      if base is BaseModel:
        continue
      parent_name = base.__name__
      if parent_name in model_map:
        row["parent_name"] = parent_name
        break

  for row in model_rows:
    parent_name = row["parent_name"]
    if not parent_name:
      continue
    cls = row["model_class"]
    parent_cls = model_classes[parent_name]
    child_only_fields = [name for name in cls.model_fields if name not in parent_cls.model_fields]
    if not child_only_fields:
      row["is_alias"] = True
      alias_map[row["element_name"]] = parent_name
      continue
    if 1 <= len(parent_cls.model_fields) <= 3:
      row["flatten_fields"] = True

  filtered_rows = [row for row in model_rows if not row["is_alias"]]
  filtered_map = {row["element_name"]: row["recid"] for row in filtered_rows}

  return filtered_rows, filtered_map, model_classes, alias_map


def resolve_annotation(
  annotation: Any,
  model_map: dict[str, int],
  alias_map: dict[str, str],
) -> dict[str, Any]:
  info = {
    "element_edt_recid": None,
    "element_is_nullable": 0,
    "element_is_list": 0,
    "element_is_dict": 0,
    "element_ref_model_recid": None,
  }

  def walk(ann: Any) -> None:
    origin = get_origin(ann)
    args = get_args(ann)

    if origin is Union:
      non_none = [arg for arg in args if arg is not type(None)]
      if len(non_none) != len(args):
        info["element_is_nullable"] = 1
      if len(non_none) == 1:
        walk(non_none[0])
      else:
        info["element_is_dict"] = 1
      return

    if ann is Any:
      info["element_is_dict"] = 1
      return

    if origin in (list,):
      info["element_is_list"] = 1
      inner = args[0] if args else Any
      walk(inner)
      return

    if origin in (dict,):
      info["element_is_dict"] = 1
      return

    if inspect.isclass(ann) and issubclass(ann, BaseModel):
      ref_model_name = resolve_alias_name(ann.__name__, alias_map)
      ref_recid = model_map.get(ref_model_name)
      if ref_recid is not None:
        info["element_ref_model_recid"] = ref_recid
      return

    edt = EDT_MAP.get(ann)
    if edt is not None:
      info["element_edt_recid"] = edt
      return

    info["element_is_dict"] = 1

  walk(annotation)
  if info["element_is_dict"] and info["element_edt_recid"] is None and info["element_ref_model_recid"] is None:
    info["element_edt_recid"] = 15
  return info


def default_value_for_field(field_info: Any) -> str | None:
  if field_info.default_factory is list:
    return "[]"
  if field_info.default_factory is dict:
    return "{}"

  default = field_info.default
  if default is PydanticUndefined:
    return None
  if default is None:
    return "null"
  if isinstance(default, bool):
    return "true" if default else "false"
  if isinstance(default, int):
    return str(default)
  if isinstance(default, str):
    return f'"{default}"'
  return None


def discover_model_fields(
  model_rows: list[dict[str, Any]],
  model_map: dict[str, int],
  model_classes: dict[str, type[BaseModel]],
  alias_map: dict[str, str],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  recid = 1

  for model in model_rows:
    model_class: type[BaseModel] = model["model_class"]
    model_recid = model["recid"]
    sort_order = 0

    fields_to_insert: list[tuple[str, Any]]
    parent_name = model["parent_name"]
    if model["flatten_fields"] and parent_name:
      parent_class = model_classes[parent_name]
      parent_fields = [
        (field_name, field_info)
        for field_name, field_info in parent_class.model_fields.items()
        if field_name != "API_PROVIDERS"
      ]
      child_only_fields = [
        (field_name, field_info)
        for field_name, field_info in model_class.model_fields.items()
        if field_name != "API_PROVIDERS" and field_name not in parent_class.model_fields
      ]
      fields_to_insert = parent_fields + child_only_fields
    else:
      fields_to_insert = [
        (field_name, field_info)
        for field_name, field_info in model_class.model_fields.items()
        if field_name != "API_PROVIDERS"
      ]

    for field_name, field_info in fields_to_insert:
      if field_name == "API_PROVIDERS":
        continue
      details = resolve_annotation(field_info.annotation, model_map, alias_map)
      row = {
        "recid": recid,
        "models_recid": model_recid,
        "element_name": field_name,
        "element_edt_recid": details["element_edt_recid"],
        "element_is_nullable": details["element_is_nullable"],
        "element_is_list": details["element_is_list"],
        "element_is_dict": details["element_is_dict"],
        "element_ref_model_recid": details["element_ref_model_recid"],
        "element_default_value": default_value_for_field(field_info),
        "element_max_length": None,
        "element_sort_order": sort_order,
        "element_status": 1,
      }
      rows.append(row)
      recid += 1
      sort_order += 1

  return rows


def parse_service_function_metadata(path: Path) -> dict[str, dict[str, Any]]:
  if not path.exists():
    return {}

  tree = ast.parse(path.read_text(), filename=str(path))
  metadata: dict[str, dict[str, Any]] = {}

  for node in tree.body:
    if not isinstance(node, ast.AsyncFunctionDef):
      continue

    module_attr: str | None = None
    method_name: str | None = None
    request_model: str | None = None
    response_model: str | None = None

    for child in ast.walk(node):
      if isinstance(child, ast.Attribute):
        chain: list[str] = []
        current: Any = child
        while isinstance(current, ast.Attribute):
          chain.append(current.attr)
          current = current.value
        if isinstance(current, ast.Name):
          chain.append(current.id)
        chain.reverse()
        if chain[:3] == ["request", "app", "state"] and len(chain) == 4:
          module_attr = chain[3]

      if isinstance(child, ast.Await) and isinstance(child.value, ast.Call):
        fn = child.value.func
        if isinstance(fn, ast.Attribute):
          if isinstance(fn.value, ast.Name) and fn.value.id in {"module", "oauth", "storage"}:
            method_name = fn.attr
            if module_attr is None:
              if fn.value.id == "oauth":
                module_attr = "auth"
              elif fn.value.id == "storage":
                module_attr = "storage"

    for stmt in node.body:
      if not isinstance(stmt, ast.Assign):
        continue
      if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
        class_name = stmt.value.func.id
        if not class_name[:1].isupper():
          continue
        target_names = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
        if any(name in {"input_payload", "data", "req"} for name in target_names):
          request_model = class_name
        if any(name in {"payload", "item"} for name in target_names):
          response_model = class_name

    metadata[node.name] = {
      "module_attr": module_attr,
      "method_name": method_name,
      "request_model": request_model,
      "response_model": response_model,
    }

  return metadata


def discover_functions(
  subdomains: list[tuple[str, str]],
  subdomain_recids: dict[tuple[str, str], int],
  model_map: dict[str, int],
  alias_map: dict[str, str],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  recid = 1

  for domain, subdomain in subdomains:
    init_file = RPC_ROOT / domain / subdomain / "__init__.py"
    services_file = RPC_ROOT / domain / subdomain / "services.py"
    operations = parse_dispatchers(init_file)
    service_meta = parse_service_function_metadata(services_file)

    for operation in operations:
      service_function = operation["service_function"]
      meta = service_meta.get(service_function or "", {})
      override_key = (domain, subdomain, operation["op"])

      module_attr = MODULE_ATTR_MAP.get((domain, subdomain)) or meta.get("module_attr") or domain
      method_name = METHOD_NAME_OVERRIDES.get(override_key) or meta.get("method_name") or operation["op"]
      request_model = REQUEST_MODEL_OVERRIDES.get(override_key) or meta.get("request_model")
      response_model = meta.get("response_model")
      if request_model:
        request_model = resolve_alias_name(request_model, alias_map)
      if response_model:
        response_model = resolve_alias_name(response_model, alias_map)

      rows.append(
        {
          "recid": recid,
          "subdomains_recid": subdomain_recids[(domain, subdomain)],
          "element_name": operation["op"],
          "element_version": operation["version"],
          "element_module_attr": module_attr,
          "element_method_name": method_name,
          "element_request_model_recid": model_map.get(request_model) if request_model else None,
          "element_response_model_recid": model_map.get(response_model) if response_model else None,
          "element_status": 1,
          "element_app_version": APP_VERSION,
          "element_iteration": 1,
        }
      )
      recid += 1

  return rows


def insert_many(cursor: pyodbc.Cursor, sql: str, rows: list[tuple[Any, ...]]) -> None:
  if not rows:
    return
  cursor.fast_executemany = True
  cursor.executemany(sql, rows)


def confirm_or_abort(force: bool) -> None:
  if force:
    return
  prompt = "reflection_rpc_* tables are not empty. Truncate and reseed? [y/N]: "
  answer = input(prompt).strip().lower()
  if answer not in {"y", "yes"}:
    print("Aborted.")
    raise SystemExit(1)


def connect() -> pyodbc.Connection:
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV") or os.environ.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("Missing AZURE_SQL_CONNECTION_STRING_DEV/AZURE_SQL_CONNECTION_STRING in environment")
  return pyodbc.connect(dsn, autocommit=True)


def main() -> None:
  parser = argparse.ArgumentParser(description="Seed reflection_rpc_* tables from rpc namespace")
  parser.add_argument("--force", action="store_true", help="Skip confirmation prompt when tables are not empty")
  args = parser.parse_args()

  domains = discover_domains()
  subdomains = discover_subdomains(domains)
  model_rows, model_map, model_classes, alias_map = discover_models()
  field_rows = discover_model_fields(model_rows, model_map, model_classes, alias_map)

  domain_recids: dict[str, int] = {name: idx for idx, name in enumerate(domains, start=1)}
  subdomain_recids: dict[tuple[str, str], int] = {
    (domain, subdomain): idx
    for idx, (domain, subdomain) in enumerate(subdomains, start=1)
  }
  function_rows = discover_functions(subdomains, subdomain_recids, model_map, alias_map)

  conn = connect()
  try:
    cursor = conn.cursor()

    count = cursor.execute("SELECT COUNT(*) FROM reflection_rpc_domains;").fetchval()
    if count and int(count) > 0:
      confirm_or_abort(args.force)

    cursor.execute("SET XACT_ABORT ON;")
    cursor.execute("BEGIN TRANSACTION;")

    cursor.execute("DELETE FROM reflection_rpc_model_fields;")
    cursor.execute("DELETE FROM reflection_rpc_functions;")
    cursor.execute("DELETE FROM reflection_rpc_models;")
    cursor.execute("DELETE FROM reflection_rpc_subdomains;")
    cursor.execute("DELETE FROM reflection_rpc_domains;")

    cursor.execute("SET IDENTITY_INSERT reflection_rpc_domains ON;")
    insert_many(
      cursor,
      """
      INSERT INTO reflection_rpc_domains (
        recid, element_name, element_required_role,
        element_is_auth_exempt, element_is_public, element_is_discord,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          domain_recids[domain],
          domain,
          DOMAIN_ROLES.get(domain),
          1 if domain == "auth" else 0,
          1 if domain == "public" else 0,
          1 if domain == "discord" else 0,
          APP_VERSION,
        )
        for domain in domains
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_domains OFF;")

    cursor.execute("SET IDENTITY_INSERT reflection_rpc_subdomains ON;")
    insert_many(
      cursor,
      """
      INSERT INTO reflection_rpc_subdomains (
        recid, domains_recid, element_name, element_entitlement_mask,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, ?, ?, 0, 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          subdomain_recids[(domain, subdomain)],
          domain_recids[domain],
          subdomain,
          APP_VERSION,
        )
        for domain, subdomain in subdomains
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_subdomains OFF;")

    cursor.execute("SET IDENTITY_INSERT reflection_rpc_models ON;")
    insert_many(
      cursor,
      """
      INSERT INTO reflection_rpc_models (
        recid, element_name, element_domain, element_subdomain, element_version,
        element_parent_recid, element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, ?, ?, ?, ?, NULL, 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["element_name"],
          row["element_domain"],
          row["element_subdomain"],
          row["element_version"],
          APP_VERSION,
        )
        for row in model_rows
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_models OFF;")

    cursor.execute("SET IDENTITY_INSERT reflection_rpc_model_fields ON;")
    insert_many(
      cursor,
      """
      INSERT INTO reflection_rpc_model_fields (
        recid, models_recid, element_name, element_edt_recid,
        element_is_nullable, element_is_list, element_is_dict,
        element_ref_model_recid, element_default_value, element_max_length,
        element_sort_order, element_status, element_created_on, element_modified_on
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["models_recid"],
          row["element_name"],
          row["element_edt_recid"],
          row["element_is_nullable"],
          row["element_is_list"],
          row["element_is_dict"],
          row["element_ref_model_recid"],
          row["element_default_value"],
          row["element_max_length"],
          row["element_sort_order"],
          row["element_status"],
        )
        for row in field_rows
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_model_fields OFF;")

    cursor.execute("SET IDENTITY_INSERT reflection_rpc_functions ON;")
    insert_many(
      cursor,
      """
      INSERT INTO reflection_rpc_functions (
        recid, subdomains_recid, element_name, element_version,
        element_module_attr, element_method_name,
        element_request_model_recid, element_response_model_recid,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["subdomains_recid"],
          row["element_name"],
          row["element_version"],
          row["element_module_attr"],
          row["element_method_name"],
          row["element_request_model_recid"],
          row["element_response_model_recid"],
          row["element_status"],
          row["element_app_version"],
          row["element_iteration"],
        )
        for row in function_rows
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_functions OFF;")

    cursor.execute("COMMIT TRANSACTION;")

    print("Seed complete:")
    print(f"  domains: {len(domains)}")
    print(f"  subdomains: {len(subdomains)}")
    print(f"  models: {len(model_rows)}")
    print(f"  model_fields: {len(field_rows)}")
    print(f"  functions: {len(function_rows)}")
  except Exception:
    try:
      cursor.execute("ROLLBACK TRANSACTION;")
    except Exception:
      pass
    raise
  finally:
    conn.close()


if __name__ == "__main__":
  main()

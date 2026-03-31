"""Seed reflection_rpc_* tables from the /rpc namespace source code."""

from __future__ import annotations

import argparse
import ast
import inspect
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Union, get_args, get_origin

import pyodbc
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import (
  REPO_ROOT,
  RPC_REFLECTION_NAMESPACE,
  find_all_model_classes,
  parse_dispatchers,
  parse_service_models,
)

load_dotenv(os.path.join(REPO_ROOT, ".env"))

RPC_ROOT = Path(REPO_ROOT) / "rpc"
APP_VERSION = "0.11.0.0"

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


def guid_for(natural_key: str) -> str:
  return str(uuid.uuid5(RPC_REFLECTION_NAMESPACE, natural_key))

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
  dict[str, str],
  dict[str, type[BaseModel]],
  dict[str, str],
]:
  model_rows: list[dict[str, Any]] = []
  model_map: dict[str, str] = {}
  model_classes: dict[str, type[BaseModel]] = {}
  alias_map: dict[str, str] = {}

  recid = 1
  raw_classes = find_all_model_classes(str(RPC_ROOT))
  for name, obj, domain, subdomain in raw_classes:
    if name in model_map:
      continue
    if not inspect.isclass(obj) or not issubclass(obj, BaseModel) or obj is BaseModel:
      continue
    if name in {"RPCRequest", "RPCResponse"}:
      continue
    match = re.search(r"(\d+)$", name)
    version = int(match.group(1)) if match else 1
    model_rows.append(
      {
        "recid": recid,
        "element_guid": guid_for(name),
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
  filtered_map = {row["element_name"]: row["element_guid"] for row in filtered_rows}

  for row in filtered_rows:
    parent_name = row["parent_name"]
    row["element_parent_guid"] = filtered_map.get(parent_name) if parent_name else None

  return filtered_rows, filtered_map, model_classes, alias_map


def topological_sort_models(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  """Sort models so parents are inserted before children."""
  by_guid: dict[str, dict[str, Any]] = {
    str(row["element_guid"]): row for row in model_rows
  }
  visited: set[str] = set()
  result: list[dict[str, Any]] = []

  def visit(row: dict[str, Any]) -> None:
    guid = str(row["element_guid"])
    if guid in visited:
      return
    parent_guid = row.get("element_parent_guid")
    if parent_guid and str(parent_guid) in by_guid:
      visit(by_guid[str(parent_guid)])
    visited.add(guid)
    result.append(row)

  for row in model_rows:
    visit(row)
  return result


def resolve_annotation(
  annotation: Any,
  model_map: dict[str, str],
  alias_map: dict[str, str],
) -> dict[str, Any]:
  info = {
    "element_edt_recid": None,
    "element_is_nullable": 0,
    "element_is_list": 0,
    "element_is_dict": 0,
    "element_ref_model_guid": None,
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
      ref_guid = model_map.get(ref_model_name)
      if ref_guid is not None:
        info["element_ref_model_guid"] = ref_guid
      return

    edt = EDT_MAP.get(ann)
    if edt is not None:
      info["element_edt_recid"] = edt
      return

    info["element_is_dict"] = 1

  walk(annotation)
  if info["element_is_dict"] and info["element_edt_recid"] is None and info["element_ref_model_guid"] is None:
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
  model_map: dict[str, str],
  model_classes: dict[str, type[BaseModel]],
  alias_map: dict[str, str],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  recid = 1

  for model in model_rows:
    model_class: type[BaseModel] = model["model_class"]
    model_guid = model["element_guid"]
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
        "element_guid": guid_for(f'{model["element_name"]}.{field_name}'),
        "models_guid": model_guid,
        "element_name": field_name,
        "element_edt_recid": details["element_edt_recid"],
        "element_is_nullable": details["element_is_nullable"],
        "element_is_list": details["element_is_list"],
        "element_is_dict": details["element_is_dict"],
        "element_ref_model_guid": details["element_ref_model_guid"],
        "element_default_value": default_value_for_field(field_info),
        "element_max_length": None,
        "element_sort_order": sort_order,
        "element_status": 1,
      }
      rows.append(row)
      recid += 1
      sort_order += 1

  return rows


def parse_service_module_metadata(path: Path) -> dict[str, dict[str, Any]]:
  if not path.exists():
    return {}

  tree = ast.parse(path.read_text(), filename=str(path))
  metadata: dict[str, dict[str, Any]] = {}

  for node in tree.body:
    if not isinstance(node, ast.AsyncFunctionDef):
      continue

    module_attr: str | None = None
    method_name: str | None = None

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
          if isinstance(fn.value, ast.Name) and fn.value.id == "module":
            method_name = fn.attr

    metadata[node.name] = {
      "module_attr": module_attr,
      "method_name": method_name,
    }

  return metadata


def discover_functions(
  subdomains: list[tuple[str, str]],
  subdomain_guids: dict[tuple[str, str], str],
  model_map: dict[str, str],
  alias_map: dict[str, str],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  recid = 1

  for domain, subdomain in subdomains:
    init_file = RPC_ROOT / domain / subdomain / "__init__.py"
    services_file = RPC_ROOT / domain / subdomain / "services.py"
    _, operations = parse_dispatchers(str(init_file))
    service_models = parse_service_models(str(services_file))
    service_meta = parse_service_module_metadata(services_file)

    for operation in operations:
      service_function = operation["func"]
      meta = service_meta.get(service_function or "", {})
      if not meta.get("module_attr") or not meta.get("method_name"):
        logging.warning(
          "Non-conforming RPC service: %s.%s.%s — module_attr=%s, method_name=%s",
          domain, subdomain, operation["op"],
          meta.get("module_attr"), meta.get("method_name"),
        )
      request_model = service_models.get(service_function)
      if request_model:
        request_model = resolve_alias_name(request_model, alias_map)

      rows.append(
        {
          "recid": recid,
          "element_guid": guid_for(
            f'{domain}.{subdomain}.{operation["op"]}.{int(operation["version"])}'
          ),
          "subdomains_guid": subdomain_guids[(domain, subdomain)],
          "element_name": operation["op"],
          "element_version": int(operation["version"]),
          "element_module_attr": meta.get("module_attr") or "",
          "element_method_name": meta.get("method_name") or "",
          "element_request_model_guid": model_map.get(request_model) if request_model else None,
          "element_response_model_guid": None,
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
  model_rows = topological_sort_models(model_rows)
  field_rows = discover_model_fields(model_rows, model_map, model_classes, alias_map)

  domain_recids: dict[str, int] = {name: idx for idx, name in enumerate(domains, start=1)}
  domain_guids: dict[str, str] = {domain: guid_for(domain) for domain in domains}
  subdomain_recids: dict[tuple[str, str], int] = {
    (domain, subdomain): idx
    for idx, (domain, subdomain) in enumerate(subdomains, start=1)
  }
  subdomain_guids: dict[tuple[str, str], str] = {
    (domain, subdomain): guid_for(f"{domain}.{subdomain}")
    for domain, subdomain in subdomains
  }
  function_rows = discover_functions(subdomains, subdomain_guids, model_map, alias_map)

  conn = connect()
  try:
    cursor = conn.cursor()

    count = cursor.execute("SELECT COUNT(*) FROM reflection_rpc_domains;").fetchval()
    if count and int(count) > 0:
      confirm_or_abort(args.force)

    cursor.execute("SET XACT_ABORT ON;")
    cursor.execute("BEGIN TRANSACTION;")

    cursor.execute(
      """
      SELECT
        element_guid,
        workflows_guid,
        element_name,
        element_description,
        functions_guid,
        dispositions_recid,
        element_sequence,
        element_is_optional,
        element_is_active,
        element_config,
        element_rollback_functions_guid,
        element_created_on,
        element_modified_on
      INTO #workflow_actions_stash
      FROM system_workflow_actions;
      """
    )
    cursor.execute("DELETE FROM system_workflow_actions;")

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
        recid, element_guid, element_name, element_required_role,
        element_is_auth_exempt, element_is_public, element_is_discord,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, ?, 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          domain_recids[domain],
          domain_guids[domain],
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
        recid, element_guid, domains_guid, element_name, element_entitlement_mask,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, 0, 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          subdomain_recids[(domain, subdomain)],
          subdomain_guids[(domain, subdomain)],
          domain_guids[domain],
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
        recid, element_guid, element_name, element_domain, element_subdomain, element_version,
        element_parent_guid, element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), 1, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["element_guid"],
          row["element_name"],
          row["element_domain"],
          row["element_subdomain"],
          row["element_version"],
          row["element_parent_guid"],
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
        recid, element_guid, models_guid, element_name, element_edt_recid,
        element_is_nullable, element_is_list, element_is_dict,
        element_ref_model_guid, element_default_value, element_max_length,
        element_sort_order, element_status, element_created_on, element_modified_on
      ) VALUES (?, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["element_guid"],
          row["models_guid"],
          row["element_name"],
          row["element_edt_recid"],
          row["element_is_nullable"],
          row["element_is_list"],
          row["element_is_dict"],
          row["element_ref_model_guid"],
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
        recid, element_guid, subdomains_guid, element_name, element_version,
        element_module_attr, element_method_name,
        element_request_model_guid, element_response_model_guid,
        element_status, element_app_version, element_iteration,
        element_created_on, element_modified_on
      ) VALUES (?, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
      """,
      [
        (
          row["recid"],
          row["element_guid"],
          row["subdomains_guid"],
          row["element_name"],
          row["element_version"],
          row["element_module_attr"],
          row["element_method_name"],
          row["element_request_model_guid"],
          row["element_response_model_guid"],
          row["element_status"],
          row["element_app_version"],
          row["element_iteration"],
        )
        for row in function_rows
      ],
    )
    cursor.execute("SET IDENTITY_INSERT reflection_rpc_functions OFF;")

    cursor.execute(
      """
      INSERT INTO system_workflow_actions (
        element_guid,
        workflows_guid,
        element_name,
        element_description,
        functions_guid,
        dispositions_recid,
        element_sequence,
        element_is_optional,
        element_is_active,
        element_config,
        element_rollback_functions_guid,
        element_created_on,
        element_modified_on
      )
      SELECT
        element_guid,
        workflows_guid,
        element_name,
        element_description,
        functions_guid,
        dispositions_recid,
        element_sequence,
        element_is_optional,
        element_is_active,
        element_config,
        element_rollback_functions_guid,
        element_created_on,
        element_modified_on
      FROM #workflow_actions_stash;
      """
    )
    cursor.execute("DROP TABLE IF EXISTS #workflow_actions_stash;")

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

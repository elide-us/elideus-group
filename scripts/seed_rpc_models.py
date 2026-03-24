from __future__ import annotations

"""Generate seed SQL for RPC model registry tables."""

import inspect
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import PydanticUndefined

from common import REPO_ROOT, load_module

sys.path.insert(0, REPO_ROOT)

RPC_ROOT = os.path.join(REPO_ROOT, 'rpc')
OUTPUT_SQL = os.path.join(REPO_ROOT, 'migrations', 'v0.10.3.1_rpc_model_seed.sql')
APP_VERSION = 'v0.10.0.10'

INPUT_SUFFIX_PATTERNS = [
  r'Get.*\d+$',
  r'Delete.*\d+$',
  r'ListBy.*\d+$',
  r'Filter\d+$',
  r'Submit.*\d+$',
  r'Approve\d+$',
  r'Reject\d+$',
  r'Reverse\d+$',
  r'Cancel\d+$',
  r'Retry\d+$',
  r'RunNow\d+$',
  r'Close\d+$',
  r'Activate\d+$',
  r'Lock\d+$',
  r'Unlock\d+$',
  r'Reopen\d+$',
  r'Consume\d+$',
  r'Expire\d+$',
  r'Shift\d+$',
  r'Generate.*\d+$',
  r'Sync.*\d+$',
  r'Set.*\d+$',
  r'Upsert.*\d+$',
  r'Create.*\d+$',
  r'Update.*\d+$',
  r'Move.*\d+$',
  r'Rename.*\d+$',
  r'Report.*\d+$',
  r'Link.*\d+$',
  r'Unlink.*\d+$',
  r'Register.*\d+$',
  r'Import\d+$',
  r'ImportInvoices\d+$',
  r'Promote\d+$',
  r'ViewThread\d+$',
  r'DeleteBefore\d+$',
  r'DeleteThread\d+$',
  r'NextNumber\d+$',
  r'Purchase\d+$',
]

REQUEST_NAME_HINTS = [
  'Request',
  'Payload',
  'Get',
  'Delete',
  'ListBy',
  'Filter',
  'Submit',
  'Approve',
  'Reject',
  'Reverse',
  'Cancel',
  'Retry',
  'RunNow',
  'Close',
  'Activate',
  'Lock',
  'Unlock',
  'Reopen',
  'Consume',
  'Expire',
  'Shift',
  'Generate',
  'Sync',
  'Set',
  'Upsert',
  'Create',
  'Update',
  'Move',
  'Rename',
  'Report',
  'Link',
  'Unlink',
  'Register',
  'Import',
  'Promote',
  'ViewThread',
  'DeleteBefore',
  'DeleteThread',
  'NextNumber',
  'Purchase',
]

OUTPUT_SUFFIX_PATTERNS = [
  r'Stats\d+$',
  r'Balance\d+$',
  r'Wallet.*\d+$',
]

PY_TYPE_TO_EDT = {
  str: 8,
  int: 1,
  float: 13,
  bool: 5,
  datetime: 7,
  date: 12,
  Decimal: 13,
  Any: 9,
  UUID: 4,
}


@dataclass
class FieldSeed:
  name: str
  ordinal: int
  edt_sql: str
  nullable: int
  default_sql: str
  is_list: int
  nested_model_name: str | None


@dataclass
class ModelSeed:
  domain: str
  subdomain: str
  cls: type[BaseModel]
  parent_name: str | None
  kind: str
  version: int
  fields: list[FieldSeed]

  @property
  def name(self) -> str:
    return self.cls.__name__


def _sql_string(value: str) -> str:
  return "'" + value.replace("'", "''") + "'"


def _default_to_sql(field: Any) -> str:
  if field.default is not PydanticUndefined:
    value = field.default
    if value is None:
      return 'NULL'
    if isinstance(value, bool):
      return _sql_string('True' if value else 'False')
    if isinstance(value, (list, dict)):
      return _sql_string(json.dumps(value))
    return _sql_string(str(value))

  default_factory = getattr(field, 'default_factory', None)
  if default_factory is list:
    return _sql_string('[]')
  if default_factory is dict:
    return _sql_string('{}')
  if default_factory is not None:
    try:
      generated = default_factory()
      if generated is None:
        return 'NULL'
      if isinstance(generated, (list, dict)):
        return _sql_string(json.dumps(generated))
      return _sql_string(str(generated))
    except Exception:
      return 'NULL'
  return 'NULL'


def _extract_version(name: str) -> int:
  match = re.search(r'(\d+)$', name)
  return int(match.group(1)) if match else 1


def _is_request_name(name: str) -> bool:
  if any(hint in name for hint in REQUEST_NAME_HINTS):
    return True
  return any(re.search(pattern, name) for pattern in INPUT_SUFFIX_PATTERNS)


def _is_response_name(name: str) -> bool:
  if 'Response' in name or 'Result' in name:
    return True
  if re.search(r'List\d+$', name):
    return True
  return any(re.search(pattern, name) for pattern in OUTPUT_SUFFIX_PATTERNS)


def _classify_kind(name: str) -> str:
  if _is_request_name(name):
    return 'request'
  if _is_response_name(name):
    return 'response'
  return 'shared'


def _unwrap_annotation(annotation: Any) -> tuple[Any, int, int, bool]:
  nullable = 0
  is_list = 0
  union_complex = False
  current = annotation

  while True:
    origin = get_origin(current)
    args = list(get_args(current))

    if origin in (list, tuple):
      is_list = 1
      current = args[0] if args else Any
      continue

    if origin in (UnionType, Union) or isinstance(current, UnionType):
      all_args = list(get_args(current))
      if any(arg in (None, NoneType) for arg in all_args):
        nullable = 1
      non_none = [arg for arg in all_args if arg not in (None, NoneType)]
      if len(non_none) == 1:
        current = non_none[0]
        continue
      union_complex = True
      current = Any
      break

    break

  return current, nullable, is_list, union_complex


def _resolve_field_type(annotation: Any, model_names: set[str]) -> tuple[str, str | None, int, int]:
  resolved, nullable, is_list, union_complex = _unwrap_annotation(annotation)

  if union_complex:
    return '9', None, nullable, is_list

  if resolved is dict:
    return '@edt_dict', None, nullable, is_list

  if inspect.isclass(resolved) and issubclass(resolved, BaseModel):
    model_name = resolved.__name__
    if model_name in model_names:
      return '2', model_name, nullable, is_list

  edt = PY_TYPE_TO_EDT.get(resolved)
  if edt is not None:
    return str(edt), None, nullable, is_list

  return '9', None, nullable, is_list


def _collect_models() -> list[ModelSeed]:
  seeds: list[ModelSeed] = []
  model_names: set[str] = set()

  candidates: list[tuple[str, str, type[BaseModel]]] = []
  for root, _, files in os.walk(RPC_ROOT):
    if 'models.py' not in files:
      continue

    rel = os.path.relpath(root, RPC_ROOT)
    parts = rel.split(os.sep)
    if len(parts) < 2:
      continue

    domain, subdomain = parts[0], parts[1]
    module_path = os.path.join(root, 'models.py')
    module = load_module(module_path)

    for _, cls in inspect.getmembers(module, inspect.isclass):
      if not issubclass(cls, BaseModel) or cls is BaseModel:
        continue
      if cls.__name__ in {'RPCRequest', 'RPCResponse'}:
        continue
      if cls.__module__ != module.__name__:
        continue
      candidates.append((domain, subdomain, cls))
      model_names.add(cls.__name__)

  for domain, subdomain, cls in candidates:
    parent_name = None
    for base in cls.__bases__:
      if inspect.isclass(base) and issubclass(base, BaseModel) and base is not BaseModel:
        if base.__name__ in model_names:
          parent_name = base.__name__
          break

    parent_fields = set()
    if parent_name:
      for base in cls.__bases__:
        if base.__name__ == parent_name:
          parent_fields = set(base.model_fields.keys())

    declared = list(getattr(cls, '__annotations__', {}).keys())
    own_field_names = [name for name in cls.model_fields.keys() if name in declared]
    if not parent_name:
      own_field_names = list(cls.model_fields.keys())
    else:
      own_field_names = [name for name in own_field_names if name not in parent_fields]

    fields: list[FieldSeed] = []
    ordinal = 1
    for field_name in cls.model_fields.keys():
      if field_name not in own_field_names:
        continue
      field = cls.model_fields[field_name]
      edt_sql, nested_model_name, nullable, is_list = _resolve_field_type(field.annotation, model_names)
      fields.append(
        FieldSeed(
          name=field_name,
          ordinal=ordinal,
          edt_sql=edt_sql,
          nullable=nullable,
          default_sql=_default_to_sql(field),
          is_list=is_list,
          nested_model_name=nested_model_name,
        )
      )
      ordinal += 1

    seeds.append(
      ModelSeed(
        domain=domain,
        subdomain=subdomain,
        cls=cls,
        parent_name=parent_name,
        kind=_classify_kind(cls.__name__),
        version=_extract_version(cls.__name__),
        fields=fields,
      )
    )

  return seeds


def _topological_sort(models: list[ModelSeed]) -> list[ModelSeed]:
  by_name = {model.name: model for model in models}
  visited: set[str] = set()
  in_progress: set[str] = set()
  ordered: list[ModelSeed] = []

  def visit(name: str) -> None:
    if name in visited:
      return
    if name in in_progress:
      return
    in_progress.add(name)
    visited.add(name)
    model = by_name[name]
    if model.parent_name and model.parent_name in by_name:
      visit(model.parent_name)
    for field in model.fields:
      if field.nested_model_name and field.nested_model_name in by_name:
        visit(field.nested_model_name)
    in_progress.discard(name)
    ordered.append(model)

  for name in sorted(by_name.keys()):
    visit(name)

  return ordered


def _render_model_sql(model: ModelSeed) -> list[str]:
  lines = [
    f'-- {model.name}' + (f' (extends {model.parent_name})' if model.parent_name else ''),
    'INSERT INTO dbo.system_schema_rpc_models',
    '  (element_name, element_domain, element_subdomain, element_version, element_kind,',
    '   element_parent_recid, element_security_roles, element_entitlements, element_app_version)',
    f"VALUES ({_sql_string(model.name)}, {_sql_string(model.domain)}, {_sql_string(model.subdomain)}, {model.version}, {_sql_string(model.kind)}, "
    + (f'@m_{model.parent_name}' if model.parent_name else 'NULL')
    + f", 0, 0, {_sql_string(APP_VERSION)});",
    f'DECLARE @m_{model.name} BIGINT = SCOPE_IDENTITY();',
  ]

  if model.fields:
    lines.extend([
      '',
      'INSERT INTO dbo.system_schema_rpc_model_fields',
      '  (models_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_is_list, element_nested_model_recid)',
      'VALUES',
    ])
    values: list[str] = []
    for field in model.fields:
      nested_sql = f'@m_{field.nested_model_name}' if field.nested_model_name else 'NULL'
      values.append(
        f"  (@m_{model.name}, {field.edt_sql}, {_sql_string(field.name)}, {field.ordinal}, {field.nullable}, {field.default_sql}, {field.is_list}, {nested_sql})"
      )
    lines.append(',\n'.join(values) + ';')
  elif model.parent_name:
    lines.extend(['', '-- No own fields (pass-through inherits parent)'])

  lines.append('GO')
  lines.append('')
  return lines


def main() -> None:
  models = _topological_sort(_collect_models())
  output: list[str] = [
    '-- Auto-generated by scripts/seed_rpc_models.py',
    '-- Seeds RPC models and fields into the registry tables.',
    '',
    "DECLARE @edt_dict BIGINT = (SELECT recid FROM dbo.system_edt_mappings WHERE element_name = 'DICT');",
    'GO',
    '',
  ]

  for model in models:
    output.extend(_render_model_sql(model))

  with open(OUTPUT_SQL, 'w') as f:
    f.write('\n'.join(output).rstrip() + '\n')

  print(f'Wrote {len(models)} models to {OUTPUT_SQL}')


if __name__ == '__main__':
  main()

from __future__ import annotations

"""Generate RPC bindings for the frontend client and shared models."""

import ast
import os
import sys
from collections import defaultdict
from typing import Iterable

import colorama
import pyodbc
from colorama import Fore, Style
from dotenv import load_dotenv

from common import HEADER_COMMENT, REPO_ROOT, camel_case

# Ensure repo root is on sys.path so RPC modules can be imported with package names.
sys.path.insert(0, REPO_ROOT)

RPC_ROOT = os.path.join(REPO_ROOT, 'rpc')
FRONTEND_RPC = os.path.join(REPO_ROOT, 'frontend', 'src', 'rpc')
FRONTEND_SHARED = os.path.join(REPO_ROOT, 'frontend', 'src', 'shared')


def urn_to_func(op: str, version: str) -> str:
  if op.startswith('get_'):
    op = op[4:]
  name = 'fetch' + camel_case(op)
  if version != '1':
    name += version
  return name


def parse_dispatchers(path: str) -> tuple[list[str], list[dict[str, str]]]:
  with open(path, 'r') as f:
    tree = ast.parse(f.read(), filename=path)

  operations: list[dict[str, str]] = []
  for node in tree.body:
    if isinstance(node, ast.Assign):
      targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
      value = node.value
    elif isinstance(node, ast.AnnAssign):
      targets = [node.target.id] if isinstance(node.target, ast.Name) else []
      value = node.value
    else:
      continue
    if 'DISPATCHERS' in targets and isinstance(value, ast.Dict):
      for key, val in zip(value.keys, value.values):
        if not (isinstance(key, ast.Tuple) and len(key.elts) == 2):
          continue
        k0, k1 = key.elts
        if not (isinstance(k0, ast.Constant) and isinstance(k1, ast.Constant)):
          continue
        op, ver = k0.value, k1.value
        if isinstance(val, ast.Name):
          func = val.id
          operations.append({'op': op, 'version': ver, 'func': func})
  rel_dir = os.path.relpath(os.path.dirname(path), RPC_ROOT)
  parts = [] if rel_dir == '.' else rel_dir.split(os.sep)
  return parts, operations


def _annotation_to_str(node: ast.AST) -> str:
  if isinstance(node, ast.Name):
    return node.id
  if isinstance(node, ast.Attribute):
    return node.attr
  if isinstance(node, ast.Subscript):
    return _annotation_to_str(node.slice)
  if isinstance(node, ast.Index):  # type: ignore[attr-defined]
    return _annotation_to_str(node.value)
  if isinstance(node, ast.Constant):
    return str(node.value)
  return 'any'


def parse_service_models(path: str) -> dict[str, str]:
  models: dict[str, str] = {}
  if not os.path.exists(path):
    return models
  with open(path, 'r') as f:
    tree = ast.parse(f.read(), filename=path)
  for node in tree.body:
    if isinstance(node, ast.AsyncFunctionDef):
      defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
      for arg, _default in zip(node.args.args, defaults):
        if arg.arg != 'payload':
          continue
        if arg.annotation is None:
          continue
        model = _annotation_to_str(arg.annotation)
        models[node.name] = model
  return models


def generate_client_ts(base: Iterable[str], ops: list[dict[str, str]], service_models: dict[str, str]) -> str:
  models = {service_models.get(o['func'], 'any') for o in ops}
  model_imports = ', '.join(sorted(m for m in models if m != 'any'))

  lines = HEADER_COMMENT.copy()

  base_list = list(base)
  rel_to_shared = '../' * (len(base_list) + 1) + 'shared/RpcModels'
  if model_imports:
    lines.append(f"import {{ rpcCall, {model_imports} }} from '{rel_to_shared}';")
  else:
    lines.append(f"import {{ rpcCall }} from '{rel_to_shared}';")

  lines.append('')

  base_urn = ':'.join(['urn'] + base_list)
  for o in ops:
    func_name = urn_to_func(o['op'], o['version'])
    model = service_models.get(o['func'], 'any')
    urn = f"{base_urn}:{o['op']}:{o['version']}"
    lines.append(f"export const {func_name} = (payload: any = null): Promise<{model}> => rpcCall('{urn}', payload);")

  lines.append('')
  return "\n".join(lines)


def write_client_bindings(base: list[str], ops: list[dict[str, str]], service_models: dict[str, str], output_dir: str) -> None:
  out_dir = os.path.join(output_dir, *base)
  os.makedirs(out_dir, exist_ok=True)
  content = generate_client_ts(base, ops, service_models)
  out_file = os.path.join(out_dir, 'index.ts')
  with open(out_file, 'w') as f:
    f.write(content)
  print(f"Wrote {out_file}")


def _python_to_ts(py_type: str | None) -> str | None:
  if not py_type:
    return None
  mapping = {
    'int': 'number',
    'bool': 'boolean',
    'str': 'string',
    'float': 'number',
    'datetime': 'string',
    'date': 'string',
    'Decimal': 'string',
    'dict': 'Record<string, any>',
    'UUID': 'string',
  }
  return mapping.get(py_type)


def _edt_to_ts(edt_name: str | None, python_type: str | None) -> str:
  by_edt = {
    'INT8': 'number',
    'INT32': 'number',
    'INT64': 'number',
    'INT64_IDENTITY': 'number',
    'UUID': 'string',
    'BOOL': 'boolean',
    'DATETIME_TZ': 'string',
    'DATE': 'string',
    'STRING': 'string',
    'TEXT': 'string',
    'DICT': 'Record<string, any>',
    'DECIMAL_19_5': 'string',
    'DECIMAL_28_12': 'string',
  }
  if edt_name in by_edt:
    return by_edt[edt_name]
  return _python_to_ts(python_type) or 'any'


def _db_connection_string() -> str:
  load_dotenv()
  candidates = [
    os.getenv('DB_CONNECTION_STRING'),
    os.getenv('AZURE_SQL_CONNECTION_STRING'),
  ]
  for value in candidates:
    if value:
      return value
  raise RuntimeError('Missing DB connection string. Set DB_CONNECTION_STRING or AZURE_SQL_CONNECTION_STRING.')


def _sorted_models(models: list[dict[str, object]]) -> list[dict[str, object]]:
  by_recid = {int(model['recid']): model for model in models}
  visited: set[int] = set()
  ordered: list[dict[str, object]] = []

  def visit(recid: int) -> None:
    if recid in visited:
      return
    visited.add(recid)
    model = by_recid[recid]
    parent_recid = model.get('element_parent_recid')
    if parent_recid is not None:
      parent_int = int(parent_recid)
      if parent_int in by_recid:
        visit(parent_int)
    ordered.append(model)

  for recid in sorted(by_recid.keys()):
    visit(recid)
  return ordered


def fetch_interfaces_from_db() -> tuple[list[dict[str, object]], dict[int, list[dict[str, object]]], dict[int, dict[str, object]]]:
  connection = pyodbc.connect(_db_connection_string())
  try:
    cursor = connection.cursor()
    cursor.execute(
      """
      SELECT recid, element_name, element_domain, element_subdomain, element_parent_recid
      FROM dbo.system_schema_rpc_models
      ORDER BY element_domain, element_subdomain, element_name
      """
    )
    model_rows = cursor.fetchall()

    models: list[dict[str, object]] = []
    for row in model_rows:
      models.append(
        {
          'recid': row.recid,
          'element_name': row.element_name,
          'element_domain': row.element_domain,
          'element_subdomain': row.element_subdomain,
          'element_parent_recid': row.element_parent_recid,
        }
      )

    cursor.execute(
      """
      SELECT
        f.recid,
        f.models_recid,
        f.edt_recid,
        f.element_name,
        f.element_ordinal,
        f.element_nullable,
        f.element_is_list,
        f.element_nested_model_recid,
        e.element_name AS edt_name,
        e.element_python_type AS edt_python_type
      FROM dbo.system_schema_rpc_model_fields f
      LEFT JOIN dbo.system_edt_mappings e ON e.recid = f.edt_recid
      ORDER BY f.models_recid, f.element_ordinal
      """
    )
    field_rows = cursor.fetchall()

    fields_by_model: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in field_rows:
      fields_by_model[int(row.models_recid)].append(
        {
          'recid': row.recid,
          'models_recid': row.models_recid,
          'edt_recid': row.edt_recid,
          'element_name': row.element_name,
          'element_ordinal': row.element_ordinal,
          'element_nullable': row.element_nullable,
          'element_is_list': row.element_is_list,
          'element_nested_model_recid': row.element_nested_model_recid,
          'edt_name': row.edt_name,
          'edt_python_type': row.edt_python_type,
        }
      )
  finally:
    connection.close()

  ordered_models = _sorted_models(models)
  by_recid = {int(model['recid']): model for model in ordered_models}
  return ordered_models, fields_by_model, by_recid


def build_ts_interface(
  model: dict[str, object],
  fields: list[dict[str, object]],
  all_models: dict[int, dict[str, object]],
) -> str:
  name = str(model['element_name'])
  parent_recid = model.get('element_parent_recid')

  if parent_recid is not None:
    parent_model = all_models[int(parent_recid)]
    parent_name = str(parent_model['element_name'])
    if not fields:
      return f'export type {name} = {parent_name};'
    lines = [f'export interface {name} extends {parent_name} {{']
  else:
    lines = [f'export interface {name} {{']

  for field in fields:
    nested_recid = field.get('element_nested_model_recid')
    if nested_recid is not None:
      base_type = str(all_models[int(nested_recid)]['element_name'])
    else:
      base_type = _edt_to_ts(
        field.get('edt_name') if isinstance(field.get('edt_name'), str) else None,
        field.get('edt_python_type') if isinstance(field.get('edt_python_type'), str) else None,
      )

    ts_type = base_type
    if int(field['element_is_list']) == 1:
      ts_type += '[]'
    if int(field['element_nullable']) == 1:
      ts_type += ' | null'

    lines.append(f"\t{field['element_name']}: {ts_type};")

  lines.append('}')
  return '\n'.join(lines)


def write_interfaces_to_file(
  models: list[dict[str, object]],
  fields_by_model: dict[int, list[dict[str, object]]],
  model_by_recid: dict[int, dict[str, object]],
  output_dir: str,
) -> None:
  interfaces: list[str] = []
  for model in models:
    recid = int(model['recid'])
    interface_text = build_ts_interface(model, fields_by_model.get(recid, []), model_by_recid)
    interfaces.append(interface_text)

  os.makedirs(output_dir, exist_ok=True)
  out_path = os.path.join(output_dir, 'RpcModels.tsx')
  with open(out_path, 'w') as f:
    lines = HEADER_COMMENT + [
      'import axios from "axios";',
      'import { getFingerprint } from "./fingerprint";',
      ''
    ]
    lines += interfaces + [''] + RPC_CALL_FUNC + ['']
    f.write("\n".join(lines))
  print(f"Wrote {len(interfaces)} TypeScript interfaces to '{out_path}'")


RPC_CALL_FUNC = [
  'export async function rpcCall<T>(op: string, payload: any = null): Promise<T> {',
  '\tconst request = {',
  '\t\top,',
  '\t\tpayload,',
  '\t\tversion: 1,',
  '\t\ttimestamp: new Date().toISOString(),',
  '\t};',
  '\tconst headers: Record<string, string> = {};',
  "\tif (typeof localStorage !== 'undefined') {",
  '\t\ttry {',
  "\t\t\tconst raw = localStorage.getItem('authTokens');",
  '\t\t\tif (raw) {',
  '\t\t\t\tconst { sessionToken } = JSON.parse(raw);',
  '\t\t\t\tif (sessionToken) headers.Authorization = `Bearer ${sessionToken}`;',
  '\t\t\t}',
  '\t\t} catch {',
  '\t\t\t/* ignore token parsing errors */',
  '\t\t}',
  '\t}',
  '\ttry {',
  "\t\tconst response = await axios.post('/rpc', request, { headers });",
  '\t\treturn response.data.payload as T;',
  '\t} catch (err: any) {',
  "\t\tif (axios.isAxiosError(err) && err.response?.status === 401) {",
  '\t\t\ttry {',
  '\t\t\t\tconst refreshReq = {',
  "\t\t\t\t\top: 'urn:auth:session:refresh_token:1',",
  '\t\t\t\t\tpayload: { fingerprint: getFingerprint() },',
  '\t\t\t\t\tversion: 1,',
  '\t\t\t\t\ttimestamp: new Date().toISOString(),',
  '\t\t\t\t};',
  "\t\t\t\tconst refreshResp = await axios.post('/rpc', refreshReq);",
  '\t\t\t\tconst newToken = refreshResp.data.payload.token;',
  "\t\t\t\tif (typeof localStorage !== 'undefined') {",
  "\t\t\t\t\tconst raw = localStorage.getItem('authTokens');",
  '\t\t\t\t\tif (raw) {',
  '\t\t\t\t\t\tconst data = JSON.parse(raw);',
  '\t\t\t\t\t\tdata.sessionToken = newToken;',
  "\t\t\t\t\t\tlocalStorage.setItem('authTokens', JSON.stringify(data));",
  '\t\t\t\t\t}',
  '\t\t\t\t}',
  '\t\t\t\theaders.Authorization = `Bearer ${newToken}`;',
  "\t\t\t\tconst retryResp = await axios.post('/rpc', request, { headers });",
  '\t\t\t\treturn retryResp.data.payload as T;',
  '\t\t\t} catch {',
  "\t\t\t\tif (typeof localStorage !== 'undefined') {",
  "\t\t\t\t\tlocalStorage.removeItem('authTokens');",
  '\t\t\t\t}',
  "\t\t\t\tif (typeof window !== 'undefined') {",
  "\t\t\t\t\twindow.dispatchEvent(new Event('sessionExpired'));",
  '\t\t\t\t}',
  '\t\t\t}',
  '\t\t}',
  '\t\tthrow err;',
  '\t}',
  '}',
]


def main() -> None:
  colorama.init()
  print('Starting RPC model extraction and TS generation...')
  models, fields_by_model, model_by_recid = fetch_interfaces_from_db()
  write_interfaces_to_file(models, fields_by_model, model_by_recid, FRONTEND_SHARED)

  print('\nStarting DISPATCHER-based RPC function generation...')
  for root, dirs, files in os.walk(RPC_ROOT):
    if '__init__.py' not in files:
      continue

    init_path = os.path.join(root, '__init__.py')
    service_path = os.path.join(root, 'services.py')
    base_parts, ops = parse_dispatchers(init_path)

    namespace = '.'.join(base_parts)
    print(f"\nFound DISPATCHERS in: {namespace}")

    if ops:
      for op in ops:
        print(f"  - RPC op: {op['op']} (v{op['version']}) → {op['func']}")
    else:
      print(f"  {Fore.YELLOW}[WARN]{Style.RESET_ALL} No valid dispatchers found, skipping.")
      continue

    service_models = parse_service_models(service_path)
    if service_models:
      print(f"  Extracted models from services.py: {', '.join(service_models.values())}")
    else:
      print(f"  {Fore.YELLOW}[WARN]{Style.RESET_ALL} No payload models found in services.py")

    write_client_bindings(base_parts, ops, service_models, FRONTEND_RPC)
  print('\nRPC function generation complete.')


if __name__ == '__main__':
  main()

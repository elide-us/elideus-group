from __future__ import annotations

"""Generate database-driven RPC models and bindings into parallel rpc2 outputs."""

import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyodbc
from dotenv import load_dotenv

from common import HEADER_COMMENT, REPO_ROOT, camel_case

PYTHON_TO_TS: dict[str, str] = {
  'int': 'number',
  'bool': 'boolean',
  'str': 'string',
  'float': 'number',
  'Decimal': 'string',
  'datetime': 'string',
  'date': 'string',
  'UUID': 'string',
  'dict': 'Record<string, any>',
}

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


def connect() -> pyodbc.Connection:
  load_dotenv(os.path.join(REPO_ROOT, '.env'))
  dsn = os.environ.get('AZURE_SQL_CONNECTION_STRING_DEV') or os.environ.get('AZURE_SQL_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('Missing AZURE_SQL_CONNECTION_STRING_DEV/AZURE_SQL_CONNECTION_STRING in environment')
  return pyodbc.connect(dsn, autocommit=True)


def to_tabs(text: str) -> str:
  lines = []
  for line in text.splitlines():
    leading = len(line) - len(line.lstrip(' '))
    tabs = '\t' * (leading // 2)
    lines.append(tabs + line.lstrip(' '))
  return '\n'.join(lines)


def urn_to_func(op: str, version: int) -> str:
  if op.startswith('get_'):
    op = op[4:]
  name = 'fetch' + camel_case(op)
  if version != 1:
    name += str(version)
  return name


def fetch_rows(cursor: pyodbc.Cursor, sql: str) -> list[dict[str, Any]]:
  cursor.execute(sql)
  cols = [col[0] for col in cursor.description]
  return [dict(zip(cols, row)) for row in cursor.fetchall()]


def build_edt_ts_map(edt_rows: list[dict[str, Any]]) -> dict[int, str]:
  edt_ts_map: dict[int, str] = {}
  for row in edt_rows:
    py_name = row['element_python_type']
    edt_ts_map[row['recid']] = PYTHON_TO_TS.get(py_name, 'any')
  return edt_ts_map


def resolve_field_type(field: dict[str, Any], edt_ts_map: dict[int, str], model_name_map: dict[int, str]) -> str:
  if field['element_is_dict']:
    base = 'Record<string, any>'
  elif field['element_ref_model_recid']:
    base = model_name_map[field['element_ref_model_recid']]
  elif field['element_edt_recid']:
    base = edt_ts_map.get(field['element_edt_recid'], 'any')
  else:
    base = 'any'

  if field['element_is_list']:
    base = f'{base}[]'
  if field['element_is_nullable']:
    base = f'{base} | null'
  return base


def merge_fields(parent_fields: list[dict[str, Any]], child_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
  merged_by_name: dict[str, dict[str, Any]] = {}
  ordered_names: list[str] = []

  for field in parent_fields:
    name = field['element_name']
    merged_by_name[name] = field
    ordered_names.append(name)

  for field in child_fields:
    name = field['element_name']
    if name not in merged_by_name:
      ordered_names.append(name)
    merged_by_name[name] = field

  return [merged_by_name[name] for name in ordered_names]


def resolve_model_fields(
  model_rows: list[dict[str, Any]],
  fields_by_model: dict[int, list[dict[str, Any]]],
) -> dict[int, list[dict[str, Any]]]:
  model_by_recid = {row['recid']: row for row in model_rows}
  resolved: dict[int, list[dict[str, Any]]] = {}

  def resolve(recid: int, stack: set[int]) -> list[dict[str, Any]]:
    if recid in resolved:
      return resolved[recid]
    if recid in stack:
      raise RuntimeError(f'Inheritance cycle detected for model recid {recid}')

    stack.add(recid)
    model = model_by_recid[recid]
    parent_recid = model['element_parent_recid']
    own_fields = list(fields_by_model.get(recid, []))

    if parent_recid:
      parent_fields = resolve(parent_recid, stack)
      merged = merge_fields(parent_fields, own_fields)
    else:
      merged = own_fields

    resolved[recid] = merged
    stack.remove(recid)
    return merged

  for model in model_rows:
    resolve(model['recid'], set())

  return resolved


def render_interface(model_name: str, fields: list[dict[str, Any]], edt_ts_map: dict[int, str], model_name_map: dict[int, str]) -> str:
  lines = [f'export interface {model_name} {{']
  for field in fields:
    field_name = field['element_name']
    field_type = resolve_field_type(field, edt_ts_map, model_name_map)
    lines.append(f'  {field_name}: {field_type};')
  lines.append('}')
  return to_tabs('\n'.join(lines))


def write_rpc_models2(interfaces: list[str]) -> Path:
  out_path = Path(REPO_ROOT) / 'frontend' / 'src' / 'shared' / 'RpcModels2.tsx'
  out_path.parent.mkdir(parents=True, exist_ok=True)

  lines = HEADER_COMMENT + [
    'import axios from "axios";',
    'import { getFingerprint } from "./fingerprint";',
    '',
  ]
  lines += interfaces + [''] + RPC_CALL_FUNC + ['']

  out_path.write_text('\n'.join(lines), encoding='utf-8')
  return out_path


def generate_binding(
  domain: str,
  subdomain: str,
  functions: list[dict[str, Any]],
  model_name_map: dict[int, str],
) -> str:
  model_imports = set()
  for fn in functions:
    resp_recid = fn['element_response_model_recid']
    if resp_recid and resp_recid in model_name_map:
      model_imports.add(model_name_map[resp_recid])

  lines = HEADER_COMMENT.copy()
  rel = '../' * 3 + 'shared/RpcModels2'
  if model_imports:
    imports = ', '.join(sorted(model_imports))
    lines.append(f"import {{ rpcCall, {imports} }} from '{rel}';")
  else:
    lines.append(f"import {{ rpcCall }} from '{rel}';")
  lines.append('')

  for fn in functions:
    func_name = urn_to_func(fn['function_name'], int(fn['element_version']))
    resp_recid = fn['element_response_model_recid']
    resp_type = model_name_map.get(resp_recid, 'any') if resp_recid else 'any'
    urn = f"urn:{domain}:{subdomain}:{fn['function_name']}:{fn['element_version']}"
    lines.append(
      f'export const {func_name} = (payload: any = null): '
      f"Promise<{resp_type}> => rpcCall('{urn}', payload);"
    )

  lines.append('')
  return '\n'.join(lines)


def write_bindings(
  functions_rows: list[dict[str, Any]],
  model_name_map: dict[int, str],
) -> tuple[int, int, int]:
  grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
  domains: set[str] = set()

  for row in functions_rows:
    domain = row['domain_name']
    subdomain = row['subdomain_name']
    grouped[(domain, subdomain)].append(row)
    domains.add(domain)

  rpc2_root = Path(REPO_ROOT) / 'frontend' / 'src' / 'rpc2'
  file_count = 0
  for (domain, subdomain), functions in sorted(grouped.items()):
    out_dir = rpc2_root / domain / subdomain
    out_dir.mkdir(parents=True, exist_ok=True)
    content = generate_binding(domain, subdomain, functions, model_name_map)
    (out_dir / 'index.ts').write_text(content, encoding='utf-8')
    file_count += 1

  return len(domains), len(grouped), file_count


def main() -> None:
  conn = connect()
  try:
    cursor = conn.cursor()

    edt_rows = fetch_rows(
      cursor,
      'SELECT recid, element_python_type FROM system_edt_mappings',
    )
    edt_ts_map = build_edt_ts_map(edt_rows)

    model_rows = fetch_rows(
      cursor,
      '''
      SELECT
        m.recid,
        m.element_name,
        p.recid AS element_parent_recid
      FROM reflection_rpc_models m
      LEFT JOIN reflection_rpc_models p
        ON p.element_guid = m.element_parent_guid
      WHERE m.element_status = 1
      ORDER BY m.element_name
      ''',
    )
    model_name_map = {row['recid']: row['element_name'] for row in model_rows}

    field_rows = fetch_rows(
      cursor,
      '''
      SELECT
        m.recid AS models_recid,
        mf.element_name,
        mf.element_edt_recid,
        mf.element_is_nullable,
        mf.element_is_list,
        mf.element_is_dict,
        rm.recid AS element_ref_model_recid,
        mf.element_sort_order
      FROM reflection_rpc_model_fields mf
      INNER JOIN reflection_rpc_models m
        ON m.element_guid = mf.models_guid
      LEFT JOIN reflection_rpc_models rm
        ON rm.element_guid = mf.element_ref_model_guid
      WHERE mf.element_status = 1
      ORDER BY m.recid, mf.element_sort_order
      ''',
    )

    fields_by_model: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in field_rows:
      fields_by_model[row['models_recid']].append(row)

    resolved_fields = resolve_model_fields(model_rows, fields_by_model)

    interfaces: list[str] = []
    for model in model_rows:
      model_name = model['element_name']
      recid = model['recid']
      interfaces.append(render_interface(model_name, resolved_fields.get(recid, []), edt_ts_map, model_name_map))

    interfaces.sort(key=lambda interface: interface.splitlines()[0])
    rpc_models_path = write_rpc_models2(interfaces)

    functions_rows = fetch_rows(
      cursor,
      '''
      SELECT fn.element_name AS function_name,
             fn.element_version,
             rm.recid AS element_response_model_recid,
             sd.element_name AS subdomain_name,
             d.element_name AS domain_name
      FROM reflection_rpc_functions fn
      LEFT JOIN reflection_rpc_models rm ON rm.element_guid = fn.element_response_model_guid
      JOIN reflection_rpc_subdomains sd ON fn.subdomains_guid = sd.element_guid
      JOIN reflection_rpc_domains d ON sd.domains_guid = d.element_guid
      WHERE fn.element_status = 1
      ORDER BY d.element_name, sd.element_name, fn.element_name
      ''',
    )

    domain_count, subdomain_count, binding_count = write_bindings(functions_rows, model_name_map)

    print(f'Wrote {len(interfaces)} interfaces to {rpc_models_path}')
    print(f'Wrote {binding_count} rpc2 binding files across {domain_count} domains and {subdomain_count} subdomains')
    print(f'Loaded {len(edt_rows)} EDT mappings, {len(model_rows)} models, {len(field_rows)} model fields, {len(functions_rows)} functions')
  finally:
    conn.close()


if __name__ == '__main__':
  main()

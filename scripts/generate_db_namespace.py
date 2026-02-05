from __future__ import annotations

"""Generate Query Registry bindings for the frontend client."""

import ast
import inspect
import os
import sys
from typing import Iterable

from pydantic import BaseModel

from scriptlib import HEADER_COMMENT, REPO_ROOT, camel_case, load_module, model_to_ts

# Ensure repo root is on sys.path so queryregistry modules can be imported with package names.
sys.path.insert(0, REPO_ROOT)

QUERY_REGISTRY_ROOT = os.path.join(REPO_ROOT, 'queryregistry')
FRONTEND_SHARED = os.path.join(REPO_ROOT, 'frontend', 'src', 'shared')


def db_op_to_func(parts: Iterable[str], op: str, version: str) -> str:
  name = 'db' + ''.join(camel_case(part) for part in parts) + camel_case(op)
  if version != '1':
    name += version
  return name


def build_db_op(parts: Iterable[str], op: str, version: str) -> str:
  return ':'.join(['db', *parts, op, version])


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
        elif isinstance(val, ast.Attribute):
          func = val.attr
        else:
          continue
        operations.append({'op': op, 'version': ver, 'func': func})
  rel_dir = os.path.relpath(os.path.dirname(path), QUERY_REGISTRY_ROOT)
  parts = [] if rel_dir == '.' else rel_dir.split(os.sep)
  return parts, operations


def to_tabs(text: str) -> str:
  lines = []
  for line in text.splitlines():
    leading = len(line) - len(line.lstrip(' '))
    tabs = '\t' * (leading // 2)
    lines.append(tabs + line.lstrip(' '))
  return "\n".join(lines)


def extract_interfaces_from_models_py(path: str, seen: set[str]) -> list[str]:
  interfaces: list[str] = []
  try:
    module = load_module(path)
  except Exception as e:
    print(f"⚠️ Skipping '{path}' due to import error: {e}")
    return interfaces

  for _, obj in inspect.getmembers(module):
    if not inspect.isclass(obj):
      continue
    if not issubclass(obj, BaseModel) or obj is BaseModel:
      continue
    if obj.__module__ != module.__name__:
      continue
    if obj.__name__ in seen:
      continue
    print(f"🧩 Found model: {obj.__name__}")
    seen.add(obj.__name__)
    interfaces.append(to_tabs(model_to_ts(obj)))

  return interfaces


def find_all_interfaces() -> list[str]:
  interfaces: list[str] = []
  seen: set[str] = set()
  for root, _, files in os.walk(QUERY_REGISTRY_ROOT):
    if 'models.py' in files:
      models_path = os.path.join(root, 'models.py')
      interfaces.extend(extract_interfaces_from_models_py(models_path, seen))
  return interfaces


def find_all_operations() -> list[dict[str, str | list[str]]]:
  operations: list[dict[str, str | list[str]]] = []
  for root, _, files in os.walk(QUERY_REGISTRY_ROOT):
    if 'handler.py' not in files:
      continue
    handler_path = os.path.join(root, 'handler.py')
    base_parts, ops = parse_dispatchers(handler_path)
    if not ops:
      continue
    namespace = '.'.join(base_parts)
    print(f"\n🧩 Found DISPATCHERS in: {namespace}")
    for op in ops:
      print(f"  • DB op: {op['op']} (v{op['version']}) → {op['func']}")
      operations.append({'parts': base_parts, 'op': op['op'], 'version': op['version']})
  return sorted(
    operations,
    key=lambda item: (
      tuple(item['parts']),
      str(item['op']),
      str(item['version']),
    ),
  )


def generate_db_namespace_ts(interfaces: list[str], operations: list[dict[str, str | list[str]]]) -> str:
  lines = HEADER_COMMENT + [
    'import axios from "axios";',
    'import { getFingerprint } from "./fingerprint";',
    '',
  ]

  lines += interfaces
  if interfaces:
    lines.append('')

  lines += DB_CALL_FUNC

  if operations:
    lines.append('')

  for op in operations:
    parts = op['parts']
    op_name = str(op['op'])
    version = str(op['version'])
    func_name = db_op_to_func(parts, op_name, version)
    db_op = build_db_op(parts, op_name, version)
    lines.append(
      f"export const {func_name} = (payload: any = null): Promise<any> => dbCall('{db_op}', payload);"
    )

  lines.append('')
  return "\n".join(lines)


def write_namespace_file(
  interfaces: list[str],
  operations: list[dict[str, str | list[str]]],
  output_dir: str,
) -> None:
  os.makedirs(output_dir, exist_ok=True)
  out_path = os.path.join(output_dir, 'DbModels.tsx')
  content = generate_db_namespace_ts(interfaces, operations)
  with open(out_path, 'w') as f:
    f.write(content)
  print(f"✅ Wrote {len(interfaces)} TypeScript interfaces to '{out_path}'")


DB_CALL_FUNC = [
  'export async function dbCall<T>(op: string, payload: any = null): Promise<T> {',
  '\tconst request = {',
  '\t\top,',
  '\t\tpayload: payload ?? {},',
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
  "\t\tconst response = await axios.post('/db', request, { headers });",
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
  "\t\t\t\tconst retryResp = await axios.post('/db', request, { headers });",
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
  print('✨ Starting Query Registry model extraction and TS generation...')
  interfaces = find_all_interfaces()
  operations = find_all_operations()
  write_namespace_file(interfaces, operations, FRONTEND_SHARED)
  print('\n🏁 Query Registry namespace generation complete.')


if __name__ == '__main__':
  main()

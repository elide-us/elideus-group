from __future__ import annotations

"""Generate RPC bindings for the frontend client and shared models."""

import ast
import inspect
import os
import sys
from typing import Iterable

from pydantic import BaseModel

from common import HEADER_COMMENT, REPO_ROOT, camel_case, load_module, model_to_ts

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
  print(f"✅ Wrote {out_file}")


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
    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
      if obj.__name__ in {'RPCRequest', 'RPCResponse'}:
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
  for root, _, files in os.walk(RPC_ROOT):
    if 'models.py' in files:
      models_path = os.path.join(root, 'models.py')
      interfaces.extend(extract_interfaces_from_models_py(models_path, seen))
  return interfaces


def write_interfaces_to_file(interfaces: list[str], output_dir: str) -> None:
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
  print(f"✅ Wrote {len(interfaces)} TypeScript interfaces to '{out_path}'")


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
  print('✨ Starting RPC model extraction and TS generation...')
  interfaces = find_all_interfaces()
  write_interfaces_to_file(interfaces, FRONTEND_SHARED)

  print('\n✨ Starting DISPATCHER-based RPC function generation...')
  for root, dirs, files in os.walk(RPC_ROOT):
    if '__init__.py' not in files:
      continue

    init_path = os.path.join(root, '__init__.py')
    service_path = os.path.join(root, 'services.py')
    base_parts, ops = parse_dispatchers(init_path)

    namespace = '.'.join(base_parts)
    print(f"\n🧩 Found DISPATCHERS in: {namespace}")

    if ops:
      for op in ops:
        print(f"  • RPC op: {op['op']} (v{op['version']}) → {op['func']}")
    else:
      print('  ⚠️ No valid dispatchers found, skipping.')
      continue

    service_models = parse_service_models(service_path)
    if service_models:
      print(f"  📦 Extracted models from services.py: {', '.join(service_models.values())}")
    else:
      print('  ⚠️ No payload models found in services.py')

    write_client_bindings(base_parts, ops, service_models, FRONTEND_RPC)
  print('\n🏁 RPC function generation complete.')


if __name__ == '__main__':
  main()

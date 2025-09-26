from __future__ import annotations

"""Generate RPC bindings (models + client functions) in one unified script."""

import ast
import asyncio
import inspect
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Iterable

from pydantic import BaseModel

from scriptlib import HEADER_COMMENT, REPO_ROOT, camel_case, load_module, model_to_ts

# Ensure repo root is on sys.path so RPC modules can be imported
sys.path.insert(0, REPO_ROOT)

RPC_ROOT = Path(REPO_ROOT, 'rpc')
FRONTEND_SHARED = Path(REPO_ROOT, 'frontend', 'src', 'shared')
FRONTEND_RPC = Path(REPO_ROOT, 'frontend', 'src', 'rpc')


@dataclass(frozen=True)
class Operation:
  op: str
  version: str
  func: str


@dataclass(frozen=True)
class DispatcherBundle:
  base_parts: tuple[str, ...]
  operations: tuple[Operation, ...]
  service_models: dict[str, str]


def _to_tabs(text: str) -> str:
  lines = []
  for line in text.splitlines():
    leading = len(line) - len(line.lstrip(' '))
    tabs = '\t' * (leading // 2)
    lines.append(tabs + line.lstrip(' '))
  return '\n'.join(lines)


def _extract_interfaces_from_models_py(path: Path, seen: set[str]) -> list[str]:
  interfaces: list[str] = []
  try:
    module = load_module(str(path))
  except Exception as exc:  # pragma: no cover - informative logging only
    print(f"⚠️ Skipping '{path}' due to import error: {exc}")
    return interfaces

  for _, obj in inspect.getmembers(module):
    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
      if obj.__name__ in {"RPCRequest", "RPCResponse"}:
        continue
      if obj.__name__ in seen:
        continue
      print(f"🧩 Found model: {obj.__name__}")
      seen.add(obj.__name__)
      interfaces.append(_to_tabs(model_to_ts(obj)))
  return interfaces


def _find_all_interfaces(root: Path) -> list[str]:
  interfaces: list[str] = []
  seen: set[str] = set()
  for dirpath, _dirs, files in os.walk(root):
    if 'models.py' not in files:
      continue
    models_path = Path(dirpath, 'models.py')
    interfaces.extend(_extract_interfaces_from_models_py(models_path, seen))
  return interfaces


def _write_models_file(interfaces: Iterable[str], output_dir: Path) -> int:
  items = list(interfaces)
  output_dir.mkdir(parents=True, exist_ok=True)
  out_path = output_dir / 'RpcModels.tsx'
  lines = list(HEADER_COMMENT)
  lines += ["import axios from \"axios\";", "import { getFingerprint } from \"./fingerprint\";", ""]
  lines += items
  lines.append('')
  lines += [
    "export async function rpcCall<T>(op: string, payload: any = null): Promise<T> {",
    "\tconst request = {",
    "\top,",
    "\tpayload,",
    "\tversion: 1,",
    "\ttimestamp: new Date().toISOString(),",
    "\t};",
    "\tconst headers: Record<string, string> = {};",
    "\tif (typeof localStorage !== 'undefined') {",
    "\t\ttry {",
    "\t\t\tconst raw = localStorage.getItem('authTokens');",
    "\t\t\tif (raw) {",
    "\t\t\t\tconst { sessionToken } = JSON.parse(raw);",
    "\t\t\t\tif (sessionToken) headers.Authorization = `Bearer ${sessionToken}`;",
    "\t\t\t}",
    "\t\t} catch {",
    "\t\t\t/* ignore token parsing errors */",
    "\t\t}",
    "\t}",
    "\ttry {",
    "\t\tconst response = await axios.post('/rpc', request, { headers });",
    "\t\treturn response.data.payload as T;",
    "\t} catch (err: any) {",
    "\t\tif (axios.isAxiosError(err) && err.response?.status === 401) {",
    "\t\t\ttry {",
    "\t\t\t\tconst refreshReq = {",
    "\t\t\t\t\top: 'urn:auth:session:refresh_token:1',",
    "\t\t\t\t\tpayload: { fingerprint: getFingerprint() },",
    "\t\t\t\t\tversion: 1,",
    "\t\t\t\t\ttimestamp: new Date().toISOString(),",
    "\t\t\t\t};",
    "\t\t\t\tconst refreshResp = await axios.post('/rpc', refreshReq);",
    "\t\t\t\tconst newToken = refreshResp.data.payload.token;",
    "\t\t\t\tif (typeof localStorage !== 'undefined') {",
    "\t\t\t\t\tconst raw = localStorage.getItem('authTokens');",
    "\t\t\t\t\tif (raw) {",
    "\t\t\t\t\t\tconst data = JSON.parse(raw);",
    "\t\t\t\t\t\tdata.sessionToken = newToken;",
    "\t\t\t\t\t\tlocalStorage.setItem('authTokens', JSON.stringify(data));",
    "\t\t\t\t\t}",
    "\t\t\t\t}",
    "\t\t\t\theaders.Authorization = `Bearer ${newToken}`;",
    "\t\t\t\tconst retryResp = await axios.post('/rpc', request, { headers });",
    "\t\t\t\treturn retryResp.data.payload as T;",
    "\t\t\t} catch {",
    "\t\t\t\tif (typeof localStorage !== 'undefined') {",
    "\t\t\t\t\tlocalStorage.removeItem('authTokens');",
    "\t\t\t\t}",
    "\t\t\t\tif (typeof window !== 'undefined') {",
    "\t\t\t\t\twindow.dispatchEvent(new Event('sessionExpired'));",
    "\t\t\t\t}",
    "\t\t\t}",
    "\t\t}",
    "\t\tthrow err;",
    "\t}",
    "}",
    '',
  ]
  out_path.write_text('\n'.join(lines), encoding='utf-8')
  return len(items)


def parse_dispatchers(path: Path | str) -> tuple[tuple[str, ...], tuple[Operation, ...]]:
  path = Path(path)
  with path.open('r', encoding='utf-8') as handle:
    tree = ast.parse(handle.read(), filename=str(path))

  operations: list[Operation] = []
  for node in tree.body:
    if isinstance(node, ast.Assign):
      targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
      value = node.value
    elif isinstance(node, ast.AnnAssign):
      targets = [node.target.id] if isinstance(node.target, ast.Name) else []
      value = node.value
    else:
      continue
    if 'DISPATCHERS' not in targets or not isinstance(value, ast.Dict):
      continue
    for key, val in zip(value.keys, value.values):
      if not (isinstance(key, ast.Tuple) and len(key.elts) == 2):
        continue
      k0, k1 = key.elts
      if not (isinstance(k0, ast.Constant) and isinstance(k1, ast.Constant)):
        continue
      if not isinstance(val, ast.Name):
        continue
      operations.append(Operation(op=str(k0.value), version=str(k1.value), func=val.id))
  rel_dir = os.path.relpath(path.parent, RPC_ROOT)
  parts: tuple[str, ...] = tuple([] if rel_dir == '.' else rel_dir.split(os.sep))
  return parts, tuple(operations)


def parse_service_models(path: Path | str) -> dict[str, str]:
  path = Path(path)
  models: dict[str, str] = {}
  if not path.exists():
    return models
  with path.open('r', encoding='utf-8') as handle:
    tree = ast.parse(handle.read(), filename=str(path))
  for node in tree.body:
    if not isinstance(node, ast.AsyncFunctionDef):
      continue
    defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults)
    for arg, _default in zip(node.args.args, defaults):
      if arg.arg != 'payload' or arg.annotation is None:
        continue
      models[node.name] = _annotation_to_str(arg.annotation)
  return models


def _annotation_to_str(node: ast.AST) -> str:
  if isinstance(node, ast.Name):
    return node.id
  if isinstance(node, ast.Attribute):
    return node.attr
  if isinstance(node, ast.Subscript):
    return _annotation_to_str(node.slice)
  if isinstance(node, ast.Index):  # pragma: no cover - python <3.9 compat
    return _annotation_to_str(node.value)
  if isinstance(node, ast.Constant):
    return str(node.value)
  return 'any'


def _bundle_dispatcher(init_path: Path) -> DispatcherBundle | None:
  base_parts, operations = parse_dispatchers(init_path)
  if not operations:
    print(f"  ⚠️ No valid dispatchers found in {init_path}")
    return None
  service_models = parse_service_models(init_path.parent / 'services.py')
  if service_models:
    print(f"  📦 Extracted models: {', '.join(sorted(service_models.values()))}")
  else:
    print("  ⚠️ No payload models found in services.py")
  return DispatcherBundle(base_parts=base_parts, operations=operations, service_models=service_models)


def _generate_ts(bundle: DispatcherBundle) -> str:
  base = bundle.base_parts
  ops = bundle.operations
  models = {bundle.service_models.get(o.func, 'any') for o in ops}
  model_imports = ', '.join(sorted(m for m in models if m != 'any'))

  lines = HEADER_COMMENT.copy()
  rel_to_shared = '../' * (len(base) + 1) + 'shared/RpcModels'
  if model_imports:
    lines.append(f"import {{ rpcCall, {model_imports} }} from '{rel_to_shared}';")
  else:
    lines.append(f"import {{ rpcCall }} from '{rel_to_shared}';")
  lines.append('')

  base_urn = ':'.join(['urn'] + list(base))
  for op in ops:
    func_name = _urn_to_func(op.op, op.version)
    model = bundle.service_models.get(op.func, 'any')
    urn = f"{base_urn}:{op.op}:{op.version}"
    lines.append(f"export const {func_name} = (payload: any = null): Promise<{model}> => rpcCall('{urn}', payload);")
  lines.append('')
  return '\n'.join(lines)


def _urn_to_func(op: str, version: str) -> str:
  if op.startswith('get_'):
    op = op[4:]
  name = 'fetch' + camel_case(op)
  if version != '1':
    name += version
  return name


async def _generate_models(shared_dir: Path) -> int:
  print('✨ Starting RPC model extraction...')
  interfaces = await asyncio.to_thread(_find_all_interfaces, RPC_ROOT)
  count = await asyncio.to_thread(_write_models_file, interfaces, shared_dir)
  print(f"✅ Wrote {count} TypeScript interfaces to '{shared_dir / 'RpcModels.tsx'}'")
  return count


async def _discover_dispatchers() -> list[DispatcherBundle]:
  bundles: list[DispatcherBundle] = []
  for root, _dirs, files in os.walk(RPC_ROOT):
    if '__init__.py' not in files:
      continue
    init_path = Path(root, '__init__.py')
    rel = os.path.relpath(root, RPC_ROOT)
    namespace = '.' if rel == '.' else rel.replace(os.sep, '.')
    print(f"\n🧩 Inspecting DISPATCHERS in: {namespace}")
    bundle = await asyncio.to_thread(_bundle_dispatcher, init_path)
    if bundle:
      bundles.append(bundle)
      for op in bundle.operations:
        print(f"  • RPC op: {op.op} (v{op.version}) → {op.func}")
  return bundles


def _write_client_bundle(bundle: DispatcherBundle, rpc_dir: Path) -> Path:
  out_dir = rpc_dir.joinpath(*bundle.base_parts)
  out_dir.mkdir(parents=True, exist_ok=True)
  content = _generate_ts(bundle)
  out_file = out_dir / 'index.ts'
  out_file.write_text(content, encoding='utf-8')
  return out_file


async def _generate_clients(rpc_dir: Path) -> int:
  print('\n✨ Starting RPC client generation...')
  bundles = await _discover_dispatchers()
  results = []
  for bundle in bundles:
    out_file = await asyncio.to_thread(_write_client_bundle, bundle, rpc_dir)
    print(f"✅ Wrote {out_file}")
    results.append(out_file)
  print('\n🏁 RPC client generation complete.')
  return len(results)


async def main(
  shared_dir: Path = FRONTEND_SHARED,
  rpc_dir: Path = FRONTEND_RPC,
  *,
  include_models: bool = True,
  include_clients: bool = True,
) -> None:
  jobs: list[tuple[str, Awaitable[int]]] = []
  if include_models:
    jobs.append(('models', _generate_models(shared_dir)))
  if include_clients:
    jobs.append(('clients', _generate_clients(rpc_dir)))

  if not jobs:
    print('Nothing to do. Enable include_models and/or include_clients.')
    return

  results = await asyncio.gather(*(job for _, job in jobs))
  summary: dict[str, int] = {}
  for (label, _), value in zip(jobs, results):
    summary[label] = value
  models_written = summary.get('models', 0)
  clients_written = summary.get('clients', 0)
  print('\nDone.')
  print(f"Generated {models_written} interfaces and {clients_written} client bundles.")


if __name__ == '__main__':
  asyncio.run(main())

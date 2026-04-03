from __future__ import annotations

"""Generate RPC bindings for the frontend client and shared models."""

import os, ast
import sys
from typing import Iterable

from colorama import Fore, Style
import colorama

from common import (
  HEADER_COMMENT,
  REPO_ROOT,
  camel_case,
  find_all_model_classes,
  model_to_ts,
  parse_dispatchers,
  parse_service_contracts,
)

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


def generate_client_ts(base: Iterable[str], ops: list[dict[str, str]], service_contracts: dict[str, dict[str, str | None]]) -> str:
  models = set()
  for op in ops:
    contract = service_contracts.get(op['func'], {})
    input_model = contract.get('input')
    output_model = contract.get('output')
    if input_model:
      models.add(input_model)
    if output_model:
      models.add(output_model)
  model_imports = ', '.join(sorted(models))

  lines = HEADER_COMMENT.copy()

  base_list = list(base)
  rel_to_shared = '../' * (len(base_list) + 1) + 'shared/RpcModels'
  if model_imports:
    lines.append(f"import {{ rpcCall, {model_imports} }} from '{rel_to_shared}';")
  else:
    lines.append(f"import {{ rpcCall }} from '{rel_to_shared}';")

  lines.append('')

  base_urn = ':'.join(['urn'] + base_list)
  for op in ops:
    func_name = urn_to_func(op['op'], op['version'])
    contract = service_contracts.get(op['func'], {})
    input_model = contract.get('input')
    output_model = contract.get('output') or 'void'
    urn = f"{base_urn}:{op['op']}:{op['version']}"
    param = f'payload: {input_model}' if input_model else 'payload: any = null'
    lines.append(f"export const {func_name} = ({param}): Promise<{output_model}> => rpcCall('{urn}', payload);")

  lines.append('')
  return "\n".join(lines)


def write_client_bindings(base: list[str], ops: list[dict[str, str]], service_contracts: dict[str, dict[str, str | None]], output_dir: str) -> None:
  out_dir = os.path.join(output_dir, *base)
  os.makedirs(out_dir, exist_ok=True)
  content = generate_client_ts(base, ops, service_contracts)
  out_file = os.path.join(out_dir, 'index.ts')
  with open(out_file, 'w') as f:
    f.write(content)
  print(f"Wrote {out_file}")


def to_tabs(text: str) -> str:
  lines = []
  for line in text.splitlines():
    leading = len(line) - len(line.lstrip(' '))
    tabs = '\t' * (leading // 2)
    lines.append(tabs + line.lstrip(' '))
  return "\n".join(lines)


def find_all_interfaces() -> list[str]:
  model_classes = find_all_model_classes(RPC_ROOT)
  return [to_tabs(model_to_ts(cls)) for _, cls, _, _ in model_classes]


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
  #interfaces = find_all_interfaces()
  interfaces = find_all_interfaces_v2()
  write_interfaces_to_file(interfaces, FRONTEND_SHARED)

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

    service_contracts = parse_service_contracts(service_path)
    if service_contracts:
      contract_lines = []
      for operation in ops:
        contract = service_contracts.get(operation['func'], {})
        contract_lines.append(
          f"{operation['func']}(input={contract.get('input')}, output={contract.get('output')})"
        )
      print(f"  Extracted contracts from services.py: {', '.join(contract_lines)}")
    else:
      print(f"  {Fore.YELLOW}[WARN]{Style.RESET_ALL} No payload contracts found in services.py")

    write_client_bindings(base_parts, ops, service_contracts, FRONTEND_RPC)
  print('\nRPC function generation complete.')

  # --- Seed RPC reflection tables (if DB is reachable) ---
  print('\nAttempting to seed reflection_rpc_* tables...')
  try:
    from scripts.seed_rpcdispatch import connect, main as seed_main
    # Test ODBC connectivity before running the full seed
    test_conn = connect()
    test_conn.close()
    # Connection succeeded — run the seed with --force (non-interactive)
    original_argv = sys.argv
    sys.argv = ['seed_rpcdispatch', '--force']
    try:
      seed_main()
    finally:
      sys.argv = original_argv
    print('RPC reflection tables seeded successfully.')
  except Exception as exc:
    print(f'  [SKIP] Could not seed reflection tables: {exc}')
    print('  This is expected in environments without ODBC (e.g., Codex).')
    print('  Reflection tables will be seeded on next build in an environment with DB access.')

# ============================================================
# V2 Model Discovery — AST-based, no imports
# ============================================================
#
# Drop-in replacement for find_all_interfaces().
# Parses models.py files as text using the ast module.
# Never imports or executes the files, so there is zero risk
# of circular-import or sys.path issues.
#
# Returns list[str] — each entry is a tab-indented TypeScript
# interface block, same shape as find_all_interfaces().
# ============================================================

# --- Type mapping (AST annotation node → TypeScript string) -----------

_PRIMITIVE_MAP: dict[str, str] = {
  "str": "string",
  "int": "number",
  "float": "number",
  "bool": "boolean",
  "dict": "Record<string, any>",
  "datetime": "string",
  "Any": "any",
}


def _ast_annotation_to_ts(node: ast.AST | None) -> str:
  """Convert a Python type annotation AST node to a TypeScript type string."""
  if node is None:
    return "any"

  # Simple name:  str, int, bool, ModelName, etc.
  if isinstance(node, ast.Name):
    return _PRIMITIVE_MAP.get(node.id, node.id)

  # Attribute access:  e.g. module.ClassName — take the attribute name
  if isinstance(node, ast.Attribute):
    return _PRIMITIVE_MAP.get(node.attr, node.attr)

  # String constant (forward reference):  "ModelName"
  if isinstance(node, ast.Constant) and isinstance(node.value, str):
    return _PRIMITIVE_MAP.get(node.value, node.value)

  # Subscript:  list[X], Optional[X], dict[K, V]
  if isinstance(node, ast.Subscript):
    base = node.value
    base_name = base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else "")

    if base_name == "list":
      inner = _ast_annotation_to_ts(node.slice)
      return f"{inner}[]"

    if base_name == "Optional":
      inner = _ast_annotation_to_ts(node.slice)
      return f"{inner} | null"

    if base_name == "dict":
      return "Record<string, any>"

    return "any"

  # BinOp with |:  str | None, int | None  (PEP 604 union syntax)
  if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
    left = _ast_annotation_to_ts(node.left)
    right = _ast_annotation_to_ts(node.right)
    if left == "None":
      left = "null"
    if right == "None":
      right = "null"
    return f"{left} | {right}"

  # None constant
  if isinstance(node, ast.Constant) and node.value is None:
    return "null"
  if isinstance(node, ast.Name) and node.id == "None":
    return "null"

  # Tuple (e.g. inside Subscript slice for dict[str, Any])
  if isinstance(node, ast.Tuple):
    return "any"

  return "any"

def _extract_models_from_file(filepath: str) -> list[dict]:
  """Parse a single models.py via AST. Return list of model descriptors.

  Each descriptor: {"name": str, "fields": [(field_name, ts_type), ...]}
  Handles local inheritance — a class inheriting from another BaseModel
  subclass in the same file is included, and inherits parent fields.
  """
  with open(filepath, "r", encoding="utf-8") as f:
    source = f.read()

  try:
    tree = ast.parse(source, filename=filepath)
  except SyntaxError:
    return []

  # First pass: collect all class nodes and their direct fields
  class_nodes: dict[str, ast.ClassDef] = {}
  class_fields: dict[str, list[tuple[str, str]]] = {}
  class_bases: dict[str, list[str]] = {}

  for node in tree.body:
    if not isinstance(node, ast.ClassDef):
      continue
    if node.name in ("RPCRequest", "RPCResponse"):
      continue

    bases = []
    for b in node.bases:
      if isinstance(b, ast.Name):
        bases.append(b.id)
      elif isinstance(b, ast.Attribute):
        bases.append(b.attr)

    class_nodes[node.name] = node
    class_bases[node.name] = bases

    fields: list[tuple[str, str]] = []
    for stmt in node.body:
      if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        fields.append((stmt.target.id, _ast_annotation_to_ts(stmt.annotation)))
    class_fields[node.name] = fields

  # Second pass: determine which classes are BaseModel descendants
  # A class is a model if it inherits from BaseModel directly, or
  # from another class in this file that is itself a model.
  is_model: dict[str, bool] = {}

  def _check_model(name: str) -> bool:
    if name in is_model:
      return is_model[name]
    if name == "BaseModel":
      return True
    if name not in class_bases:
      return False
    # Prevent infinite recursion on weird inheritance
    is_model[name] = False
    result = any(_check_model(b) for b in class_bases[name])
    is_model[name] = result
    return result

  for name in class_nodes:
    _check_model(name)

  # Third pass: resolve inherited fields and build output
  resolved_fields: dict[str, list[tuple[str, str]]] = {}

  def _resolve_fields(name: str) -> list[tuple[str, str]]:
    if name in resolved_fields:
      return resolved_fields[name]
    if name not in class_nodes:
      return []

    # Start with parent fields (in order)
    inherited: list[tuple[str, str]] = []
    for base_name in class_bases[name]:
      if base_name != "BaseModel" and base_name in class_nodes:
        inherited = _resolve_fields(base_name).copy()

    # Merge own fields — own fields override parent fields by name
    own = class_fields[name]
    own_names = {f[0] for f in own}
    merged = [(n, t) for n, t in inherited if n not in own_names] + own
    resolved_fields[name] = merged
    return merged

  models = []
  for name in class_nodes:
    if not is_model.get(name, False):
      continue
    fields = _resolve_fields(name)
    models.append({"name": name, "fields": fields})

  return models

def _model_dict_to_ts(model: dict) -> str:
  """Convert a model descriptor to a tab-indented TypeScript interface."""
  name = model["name"]
  fields = model["fields"]
  if not fields:
    return f"export type {name} = Record<string, never>;"
  lines = [f"export interface {name} {{"]
  for field_name, ts_type in fields:
    lines.append(f"\t{field_name}: {ts_type};")
  lines.append("}")
  return "\n".join(lines)


def find_all_interfaces_v2() -> list[str]:
  """Walk RPC_ROOT, parse every models.py via AST, return TS interfaces.

  Drop-in replacement for find_all_interfaces().
  """
  seen: set[str] = set()
  interfaces: list[str] = []

  for root, _, files in os.walk(RPC_ROOT):
    if "models.py" not in files:
      continue
    models_path = os.path.join(root, "models.py")
    models = _extract_models_from_file(models_path)
    for model in models:
      if model["name"] in seen:
        continue
      seen.add(model["name"])
      interfaces.append(_model_dict_to_ts(model))

  return interfaces

if __name__ == '__main__':
  main()

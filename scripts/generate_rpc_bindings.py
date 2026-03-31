from __future__ import annotations

"""Generate RPC bindings for the frontend client and shared models."""

import os
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
  interfaces = find_all_interfaces()
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


if __name__ == '__main__':
  main()

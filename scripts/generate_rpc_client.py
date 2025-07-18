from __future__ import annotations
import os, re

from genlib import REPO_ROOT, HEADER_COMMENT, camel_case

RPC_ROOT = os.path.join(REPO_ROOT, 'rpc')
FRONTEND_RPC = os.path.join(REPO_ROOT, 'frontend', 'src', 'rpc')

CASE_RE = re.compile(r'case \["([^\"]+)",\s*"([^\"]+)"\]:')
FUNC_RE = re.compile(r'services\.([A-Za-z0-9_]+)')
PAYLOAD_RE = re.compile(r'payload\s*=\s*([A-Za-z0-9_]+)\(')

def urn_to_func(op: str) -> str:
  if op.startswith('get_'):
    op = op[4:]
  return 'fetch' + camel_case(op)

def parse_service_models(path: str) -> dict[str, str]:
  models: dict[str, str] = {}
  if not os.path.exists(path):
    return models
  with open(path, 'r') as f:
    lines = f.readlines()
  current = None
  for line in lines:
    func = re.match(r'async def (\w+)\(', line)
    if func:
      current = func.group(1)
      continue
    m = PAYLOAD_RE.search(line)
    if m and current:
      models[current] = m.group(1)
      current = None
  return models

def parse_handler(path: str) -> tuple[list[str], list[dict[str, str]]]:
  with open(path, 'r') as f:
    lines = f.readlines()
  operations: list[dict[str, str]] = []
  for idx, line in enumerate(lines):
    case = CASE_RE.search(line)
    if case:
      op, ver = case.groups()
      func = ''
      for look in range(idx + 1, idx + 3):
        if look < len(lines):
          m = FUNC_RE.search(lines[look])
          if m:
            func = m.group(1)
            break
      operations.append({'op': op, 'version': ver, 'func': func})
  rel_dir = os.path.relpath(os.path.dirname(path), RPC_ROOT)
  parts = rel_dir.split(os.sep)
  return parts, operations

def generate_ts(base: list[str], ops: list[dict[str, str]], service_models: dict[str, str]) -> str:
  models = {service_models.get(o['func'], 'any') for o in ops}
  model_imports = ', '.join(sorted(m for m in models if m != 'any'))

  lines = HEADER_COMMENT.copy()

  if model_imports:
    lines.append(f"import {{ rpcCall, {model_imports} }} from '../../../shared/RpcModels';")
  else:
    lines.append("import { rpcCall } from '../../../shared/RpcModels';")

  lines.append('')

  base_urn = ':'.join(['urn'] + base)
  for o in ops:
    func_name = urn_to_func(o['op'])
    model = service_models.get(o['func'], 'any')
    urn = f"{base_urn}:{o['op']}:{o['version']}"
    lines.append(f"export const {func_name} = (payload: any = null): Promise<{model}> => rpcCall('{urn}', payload);")

  lines.append('')
  return "\n".join(lines)

def main(output_dir: str = FRONTEND_RPC) -> None:
  for root, dirs, files in os.walk(RPC_ROOT):
    if 'handler.py' not in files:
      continue
    handler_path = os.path.join(root, 'handler.py')
    service_path = os.path.join(root, 'services.py')
    base_parts, ops = parse_handler(handler_path)
    service_models = parse_service_models(service_path)
    if not ops:
      continue
    out_dir = os.path.join(output_dir, *base_parts)
    os.makedirs(out_dir, exist_ok=True)
    content = generate_ts(base_parts, ops, service_models)
    with open(os.path.join(out_dir, 'index.ts'), 'w') as f:
      f.write(content)
    print(f"✅ Wrote {os.path.join(out_dir, 'index.ts')}")

if __name__ == '__main__':
  main()

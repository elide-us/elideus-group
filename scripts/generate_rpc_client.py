from __future__ import annotations
import ast, os

"""Generate TypeScript RPC client functions by parsing Python sources.

This version uses the Python AST to read DISPATCHERS mappings and payload
models rather than brittle regular expressions.
"""

from genlib import REPO_ROOT, HEADER_COMMENT, camel_case

RPC_ROOT = os.path.join(REPO_ROOT, 'rpc')
FRONTEND_RPC = os.path.join(REPO_ROOT, 'frontend', 'src', 'rpc')


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
    func_name = urn_to_func(o['op'], o['version'])
    model = service_models.get(o['func'], 'any')
    urn = f"{base_urn}:{o['op']}:{o['version']}"
    lines.append(f"export const {func_name} = (payload: any = null): Promise<{model}> => rpcCall('{urn}', payload);")

  lines.append('')
  return "\n".join(lines)


def main(output_dir: str = FRONTEND_RPC) -> None:
  print("✨ Starting DISPATCHER-based RPC function generation...")
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
      print("  ⚠️ No valid dispatchers found, skipping.")
      continue

    service_models = parse_service_models(service_path)
    if service_models:
      print(f"  📦 Extracted models from services.py: {', '.join(service_models.values())}")
    else:
      print("  ⚠️ No payload models found in services.py")

    out_dir = os.path.join(output_dir, *base_parts)
    os.makedirs(out_dir, exist_ok=True)
    content = generate_ts(base_parts, ops, service_models)
    out_file = os.path.join(out_dir, 'index.ts')
    with open(out_file, 'w') as f:
      f.write(content)
    print(f"✅ Wrote {out_file}")
  print("\n🏁 RPC function generation complete.")


if __name__ == '__main__':
  main()

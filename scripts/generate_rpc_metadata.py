from __future__ import annotations
import os, json
from pathlib import Path
from generate_rpc_client import parse_handler
from genlib import REPO_ROOT

RPC_ROOT = Path(REPO_ROOT) / 'rpc'
METADATA_FILE = RPC_ROOT / 'metadata.json'


def gather_ops() -> dict[str, int]:
  metadata: dict[str, int] = {}
  missing: list[str] = []
  for root, dirs, files in os.walk(RPC_ROOT):
    if 'handler.py' not in files:
      continue
    handler_path = os.path.join(root, 'handler.py')
    base_parts, ops = parse_handler(handler_path)
    for op in ops:
      urn = ':'.join(['urn'] + base_parts + [op['op'], op['version']])
      metadata.setdefault(urn, 0)
  return metadata


def load_existing() -> dict[str, int]:
  if METADATA_FILE.exists():
    with open(METADATA_FILE, 'r') as f:
      data = json.load(f)
    return {item['op']: item.get('capabilities', 0) for item in data.get('rpc', [])}
  return {}


def write_metadata(data: dict[str, int]):
  out = {'rpc': [{'op': k, 'capabilities': v} for k, v in sorted(data.items())]}
  METADATA_FILE.write_text(json.dumps(out, indent=2))


def main() -> None:
  ops = gather_ops()
  existing = load_existing()
  merged = {op: existing.get(op, cap) for op, cap in ops.items()}
  missing = [op for op, cap in merged.items() if cap == 0]
  write_metadata(merged)
  if missing:
    print('⚠️ Missing capability metadata for:')
    for op in missing:
      print(f'  - {op}')
  else:
    print('✅ RPC metadata written')


if __name__ == '__main__':
  main()


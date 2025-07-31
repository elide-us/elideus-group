from __future__ import annotations
import os, json
from pathlib import Path
from generate_rpc_client import parse_dispatchers
from genlib import REPO_ROOT

RPC_ROOT = Path(REPO_ROOT) / 'rpc'
METADATA_FILE = RPC_ROOT / 'metadata.json'


def gather_ops() -> dict[str, int]:
  metadata: dict[str, int] = {}
  for root, dirs, files in os.walk(RPC_ROOT):
    if '__init__.py' not in files:
      continue
    init_path = os.path.join(root, '__init__.py')
    base_parts, ops = parse_dispatchers(init_path)
    if not ops:
      continue
    print(f"\n📦 Found DISPATCHERS in: {'.'.join(base_parts)}")
    for op in ops:
      urn = ':'.join(['urn'] + base_parts + [op['op'], op['version']])
      print(f"  • {urn}")
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
  print("✨ Scanning RPC namespaces for capability metadata...")
  ops = gather_ops()
  existing = load_existing()
  merged = {op: existing.get(op, cap) for op, cap in ops.items()}
  missing = [op for op, cap in merged.items() if cap == 0]
  write_metadata(merged)

  if missing:
    print("\n⚠️ Missing capability metadata for:")
    for op in missing:
      print(f"  - {op}")
  else:
    print("\n✅ All RPC entries have capability metadata!")


if __name__ == '__main__':
  main()

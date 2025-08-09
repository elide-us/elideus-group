from __future__ import annotations
import os, json
from pathlib import Path
from generate_rpc_client import parse_dispatchers
from genlib import REPO_ROOT

RPC_ROOT = Path(REPO_ROOT) / 'rpc'
METADATA_FILE = RPC_ROOT / 'metadata.json'


def gather_ops() -> dict:
  tree: dict[str, dict] = {}
  for root, dirs, files in os.walk(RPC_ROOT):
    if '__init__.py' not in files:
      continue
    init_path = os.path.join(root, '__init__.py')
    base_parts, ops = parse_dispatchers(init_path)
    if not ops:
      continue
    print(f"\n📦 Found DISPATCHERS in: {'.'.join(base_parts)}")
    domain = base_parts[0]
    subdomain = base_parts[1] if len(base_parts) > 1 else 'general'
    dom = tree.setdefault(domain, {'subdomains': {}})
    sub = dom['subdomains'].setdefault(subdomain, {'functions': []})
    for op in ops:
      urn = ':'.join(['urn'] + base_parts + [op['op'], op['version']])
      print(f"  • {urn}")
      sub['functions'].append({'op': urn, 'capabilities': 0})
  return tree


def load_existing() -> dict[str, int]:
  if METADATA_FILE.exists():
    with open(METADATA_FILE, 'r') as f:
      data = json.load(f)
    existing: dict[str, int] = {}
    rpc_section = data.get('rpc', {})
    if isinstance(rpc_section, list):
      for item in rpc_section:
        existing[item['op']] = item.get('capabilities', 0)
      return existing
    for dom in rpc_section.get('domains', []):
      for sub in dom.get('subdomains', []):
        for fn in sub.get('functions', []):
          existing[fn['op']] = fn.get('capabilities', 0)
    return existing
  return {}


def write_metadata(tree: dict):
  for dom in tree.values():
    for sub in dom['subdomains'].values():
      sub['capabilities'] = sum(f['capabilities'] for f in sub['functions'])
    dom['capabilities'] = sum(sub['capabilities'] for sub in dom['subdomains'].values())
  total = sum(dom['capabilities'] for dom in tree.values())
  out = {
    'rpc': {
      'capabilities': total,
      'domains': [
        {
          'domain': d,
          'capabilities': dom['capabilities'],
          'subdomains': [
            {
              'subdomain': s,
              'capabilities': sub['capabilities'],
              'functions': sorted(sub['functions'], key=lambda f: f['op'])
            }
            for s, sub in sorted(dom['subdomains'].items())
          ]
        }
        for d, dom in sorted(tree.items())
      ]
    }
  }
  METADATA_FILE.write_text(json.dumps(out, indent=2))


def main() -> None:
  print("✨ Scanning RPC namespaces for capability metadata...")
  tree = gather_ops()
  existing = load_existing()
  for dom in tree.values():
    for sub in dom['subdomains'].values():
      for fn in sub['functions']:
        fn['capabilities'] = existing.get(fn['op'], fn['capabilities'])
  write_metadata(tree)

  missing: list[str] = []
  for dom in tree.values():
    for sub in dom['subdomains'].values():
      for fn in sub['functions']:
        if fn['capabilities'] == 0:
          missing.append(fn['op'])
  if missing:
    print("\n⚠️ Missing capability metadata for:")
    for op in missing:
      print(f"  - {op}")
  else:
    print("\n✅ All RPC entries have capability metadata!")


if __name__ == '__main__':
  main()

import json
import os
import subprocess
from pathlib import Path


def get_latest_tag() -> str:
  try:
    tags = subprocess.check_output(['git', 'tag', '--list', 'v*', '--sort=-v:refname'], text=True).split()
    return tags[0] if tags else 'v0.0.0'
  except Exception:
    return 'v0.0.0'


def get_short_commit() -> str:
  try:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
  except Exception:
    return 'unknown'

def main() -> None:
  tag = get_latest_tag()
  commit = get_short_commit()
  data = {'tag': tag, 'commit': commit}
  Path('version.json').write_text(json.dumps(data))
  print('version.json updated:', data)


if __name__ == '__main__':
  main()

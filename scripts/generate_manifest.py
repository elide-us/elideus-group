from __future__ import annotations
import inspect, json
from importlib import import_module
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from server.modules import BaseModule
from server.modules.providers import (
  AuthProvider,
  AuthProviderBase,
  BaseProvider,
  DbProviderBase,
  LifecycleProvider,
)


def _collect_modules() -> dict[str, str]:
  modules: dict[str, str] = {}
  for path in Path('server/modules').glob('*_module.py'):
    name = path.stem[:-7]
    mod = import_module(f'server.modules.{path.stem}')
    for attr in mod.__dict__.values():
      if inspect.isclass(attr) and issubclass(attr, BaseModule) and attr is not BaseModule:
        modules[name] = f'{mod.__name__}.{attr.__name__}'
  return modules


def _collect_providers() -> dict[str, str]:
  providers: dict[str, str] = {}
  base = Path('server/modules/providers')
  for path in base.rglob('*.py'):
    if path.name == '__init__.py' and path.parent == base:
      continue
    pkg = '.'.join((path.parent if path.name == '__init__.py' else path.with_suffix('')).parts)
    mod = import_module(pkg)
    for attr in mod.__dict__.values():
      if inspect.isclass(attr) and attr not in {
        AuthProviderBase,
        DbProviderBase,
        AuthProvider,
        BaseProvider,
        LifecycleProvider,
      }:
        if issubclass(attr, AuthProviderBase) or issubclass(attr, DbProviderBase):
          providers[attr.__name__] = f'{mod.__name__}.{attr.__name__}'
  return providers


def main() -> None:
  manifest = {
    'modules': _collect_modules(),
    'providers': _collect_providers(),
  }
  with open('manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
  print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
  main()

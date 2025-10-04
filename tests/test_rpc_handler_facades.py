import asyncio
import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from server.modules import ModuleServices


HANDLER_PATHS = list(Path('rpc').glob('*/handler.py'))


def _iter_handler_paths():
  for path in HANDLER_PATHS:
    yield path
  yield Path('rpc/handler.py')


def test_rpc_handlers_do_not_import_module_internals():
  for path in _iter_handler_paths():
    if not path.exists():
      continue
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
      if isinstance(node, ast.Import):
        for alias in node.names:
          if alias.name.startswith('server.modules.'):
            pytest.fail(f"{path} imports module internals via '{alias.name}'")
      if isinstance(node, ast.ImportFrom):
        module = node.module or ''
        if module.startswith('server.modules') and module != 'server.modules':
          pytest.fail(f"{path} imports module internals via '{module}'")


class _DenyAuthService:
  def __init__(self):
    self.required_names: list[str] = []

  def require_role_mask(self, name: str) -> int:
    self.required_names.append(name)
    return 1

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    return False


@pytest.mark.parametrize('module_name, handler_name', [
  ('rpc.account.handler', 'handle_account_request'),
  ('rpc.moderation.handler', 'handle_moderation_request'),
  ('rpc.service.handler', 'handle_service_request'),
  ('rpc.storage.handler', 'handle_storage_request'),
  ('rpc.support.handler', 'handle_support_request'),
  ('rpc.system.handler', 'handle_system_request'),
  ('rpc.users.handler', 'handle_users_request'),
  ('rpc.discord.handler', 'handle_discord_request'),
])
def test_rpc_handlers_deny_unauthorised_access(monkeypatch, module_name, handler_name):
  module = importlib.import_module(module_name)
  handler = getattr(module, handler_name)

  call_tracker = {'invoked': False}

  async def noop_handler(parts, request):
    call_tracker['invoked'] = True

  monkeypatch.setattr(module, 'HANDLERS', {'noop': noop_handler})
  if hasattr(module, 'REQUIRED_ROLES'):
    monkeypatch.setattr(module, 'REQUIRED_ROLES', {'noop': 'ROLE_TEST'})
  if hasattr(module, 'FORBIDDEN_DETAILS'):
    monkeypatch.setattr(module, 'FORBIDDEN_DETAILS', {})

  async def fake_unbox_request(request):
    return SimpleNamespace(op='urn:test', version='1'), SimpleNamespace(user_guid='user', role_mask=0), []

  monkeypatch.setattr(module, 'unbox_request', fake_unbox_request)

  app = FastAPI()
  services = ModuleServices()
  app.state.services = services
  services.auth = _DenyAuthService()

  scope = {
    'type': 'http',
    'http_version': '1.1',
    'scheme': 'http',
    'app': app,
    'headers': [],
    'path': '/',
    'method': 'POST',
    'query_string': b'',
  }
  request = Request(scope)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(handler(['noop'], request))

  assert exc.value.status_code == 403
  assert call_tracker['invoked'] is False

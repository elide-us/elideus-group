import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
rpc_discord_pkg = types.ModuleType('rpc.discord')
rpc_discord_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/discord')]
sys.modules.setdefault('rpc.discord', rpc_discord_pkg)

rpc_discord_personas_pkg = types.ModuleType('rpc.discord.personas')
rpc_discord_personas_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/discord/personas')]
sys.modules.setdefault('rpc.discord.personas', rpc_discord_personas_pkg)

server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
discord_personas_module_pkg = types.ModuleType('server.modules.discord_personas_module')
models_pkg = types.ModuleType('server.models')


class DiscordPersonasModule:
  def __init__(self):
    self.personas = [
      {
        'recid': 1,
        'name': 'uwu',
        'prompt': 'owo',
        'tokens': 512,
        'models_recid': 2,
        'model': 'gpt-4',
      }
    ]
    self.models = [
      {
        'recid': 2,
        'name': 'gpt-4',
      }
    ]
    self.upserts: list[dict] = []
    self.deletes: list[tuple[int | None, str | None]] = []

  async def list_personas(self):
    return self.personas

  async def list_models(self):
    return self.models

  async def upsert_persona(self, payload: dict):
    self.upserts.append(payload)

  async def delete_persona(self, recid: int | None = None, name: str | None = None):
    self.deletes.append((recid, name))


discord_personas_module_pkg.DiscordPersonasModule = DiscordPersonasModule
modules_pkg.discord_personas_module = discord_personas_module_pkg
server_pkg.modules = modules_pkg


class RPCResponse:
  def __init__(self, **data):
    self.__dict__.update(data)


models_pkg.RPCResponse = RPCResponse
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.discord_personas_module', discord_personas_module_pkg)
sys.modules.setdefault('server.models', models_pkg)

svc_spec = importlib.util.spec_from_file_location(
  'rpc.discord.personas.services',
  pathlib.Path(__file__).resolve().parent.parent / 'rpc/discord/personas/services.py',
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules['rpc.discord.personas.services'] = svc
svc_spec.loader.exec_module(svc)

discord_personas_get_personas_v1 = svc.discord_personas_get_personas_v1
discord_personas_get_models_v1 = svc.discord_personas_get_models_v1
discord_personas_upsert_persona_v1 = svc.discord_personas_upsert_persona_v1
discord_personas_delete_persona_v1 = svc.discord_personas_delete_persona_v1


async def fake_unbox(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='user', roles=['ROLE_DISCORD_ADMIN'])
  return rpc_req, auth_ctx, None


svc.unbox_request = fake_unbox


db = DiscordPersonasModule()

app = FastAPI()
app.state.discord_personas = db


@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  op = body['op']
  if op == 'urn:discord:personas:get_personas:1':
    return await discord_personas_get_personas_v1(request)
  if op == 'urn:discord:personas:get_models:1':
    return await discord_personas_get_models_v1(request)
  if op == 'urn:discord:personas:upsert_persona:1':
    return await discord_personas_upsert_persona_v1(request)
  if op == 'urn:discord:personas:delete_persona:1':
    return await discord_personas_delete_persona_v1(request)
  raise AssertionError('unexpected op')


client = TestClient(app)


def test_get_personas_service():
  resp = client.post('/rpc', json={'op': 'urn:discord:personas:get_personas:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'personas': [
      {
        'recid': 1,
        'name': 'uwu',
        'prompt': 'owo',
        'tokens': 512,
        'models_recid': 2,
        'model': 'gpt-4',
      }
    ]
  }


def test_get_models_service():
  resp = client.post('/rpc', json={'op': 'urn:discord:personas:get_models:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'models': [
      {
        'recid': 2,
        'name': 'gpt-4',
      }
    ]
  }


def test_upsert_and_delete_persona_service():
  upsert_payload = {
    'recid': 1,
    'name': 'uwu',
    'prompt': 'new prompt',
    'tokens': 1024,
    'models_recid': 2,
  }
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:personas:upsert_persona:1', 'payload': upsert_payload},
  )
  assert resp.status_code == 200
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:personas:delete_persona:1', 'payload': {'recid': 1}},
  )
  assert resp.status_code == 200
  assert db.upserts == [upsert_payload]
  assert db.deletes == [(1, None)]

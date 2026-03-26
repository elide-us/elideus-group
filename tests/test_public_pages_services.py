import pathlib
import sys
import types

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Stub server package with minimal models
server_pkg = types.ModuleType('server')
models_pkg = types.ModuleType('server.models')

from pydantic import BaseModel


class RPCRequest(BaseModel):
  op: str
  payload: dict | None = None
  version: int = 1


class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int = 1


class AuthContext(BaseModel):
  role_mask: int = 0


models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg
sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.models', models_pkg)


def test_public_pages_dispatchers_registered():
  from rpc.public.pages import DISPATCHERS

  assert set(DISPATCHERS.keys()) == {
    ("list_pages", "1"),
    ("get_page", "1"),
  }


def test_public_pages_handler_registered_in_public_handlers():
  from rpc.public import HANDLERS
  from rpc.public.pages.handler import handle_pages_request

  assert HANDLERS["pages"] is handle_pages_request

import asyncio
from fastapi import FastAPI, Request
from rpc.account.users.services import get_users_v2
from rpc.system.routes.services import list_routes_v2
from server.modules.database_provider import DatabaseProvider

class MockProvider(DatabaseProvider):
  async def select_user(self, *args, **kwargs):
    raise NotImplementedError
  async def insert_user(self, *args, **kwargs):
    raise NotImplementedError
  async def get_user_profile(self, *args, **kwargs):
    raise NotImplementedError
  async def get_user_roles(self, *args, **kwargs):
    raise NotImplementedError
  async def list_roles(self, *args, **kwargs):
    raise NotImplementedError
  async def set_role(self, *args, **kwargs):
    raise NotImplementedError
  async def delete_role(self, *args, **kwargs):
    raise NotImplementedError
  async def get_user_enablements(self, *args, **kwargs):
    raise NotImplementedError
  async def select_routes(self, *args, **kwargs):
    raise NotImplementedError
  async def list_routes(self):
    return [{
      'element_path': '/p',
      'element_name': 'P',
      'element_icon': 'i',
      'element_roles': 0,
      'element_sequence': 1,
    }]
  async def set_route(self, *args, **kwargs):
    raise NotImplementedError
  async def delete_route(self, *args, **kwargs):
    raise NotImplementedError
  async def select_links(self, *args, **kwargs):
    raise NotImplementedError
  async def get_config_value(self, *args, **kwargs):
    raise NotImplementedError
  async def set_config_value(self, *args, **kwargs):
    raise NotImplementedError
  async def list_config(self, *args, **kwargs):
    raise NotImplementedError
  async def delete_config_value(self, *args, **kwargs):
    raise NotImplementedError
  async def update_display_name(self, *args, **kwargs):
    raise NotImplementedError
  async def select_users(self):
    return [{'guid': 'u', 'display_name': 'User'}]
  async def select_users_with_role(self, *args, **kwargs):
    raise NotImplementedError
  async def select_users_without_role(self, *args, **kwargs):
    raise NotImplementedError
  async def set_user_roles(self, *args, **kwargs):
    raise NotImplementedError
  async def set_user_credits(self, *args, **kwargs):
    raise NotImplementedError
  async def set_user_rotation_token(self, *args, **kwargs):
    raise NotImplementedError
  async def create_user_session(self, *args, **kwargs):
    raise NotImplementedError
  async def get_session_by_rotation(self, *args, **kwargs):
    raise NotImplementedError
  async def update_session_tokens(self, *args, **kwargs):
    raise NotImplementedError
  async def delete_session(self, *args, **kwargs):
    raise NotImplementedError
  async def get_user_profile_image(self, *args, **kwargs):
    raise NotImplementedError
  async def set_user_profile_image(self, *args, **kwargs):
    raise NotImplementedError


def test_get_users_with_mock_provider():
  app = FastAPI()
  app.state.mssql = MockProvider()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  resp = asyncio.run(get_users_v2(req))
  assert resp.payload.users[0].displayName == 'User'


def test_list_routes_with_mock_provider():
  app = FastAPI()
  app.state.mssql = MockProvider()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  resp = asyncio.run(list_routes_v2(req))
  assert resp.payload.routes[0].path == '/p'

import asyncio
import pyodbc
from server.helpers import roles as role_helper

class DummyDB:
  async def list_roles(self):
    raise pyodbc.Error()


def test_load_roles_handles_missing_table():
  prev = role_helper.ROLES.copy()
  prev_names = role_helper.ROLE_NAMES[:]
  prev_reg = role_helper.ROLE_REGISTERED
  try:
    asyncio.run(role_helper.load_roles(DummyDB()))
    assert role_helper.ROLES == prev
    assert role_helper.ROLE_NAMES == prev_names
    assert role_helper.ROLE_REGISTERED == prev_reg
  finally:
    role_helper.ROLES = prev
    role_helper.ROLE_NAMES = prev_names
    role_helper.ROLE_REGISTERED = prev_reg

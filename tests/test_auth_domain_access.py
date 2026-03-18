import asyncio

from fastapi import FastAPI, HTTPException
import pytest

from server.modules.auth_module import AuthModule


def test_check_domain_access_rejects_unconfigured_domain():
  auth = AuthModule(FastAPI())
  auth.domain_role_map = {}

  with pytest.raises(HTTPException) as exc:
    asyncio.run(auth.check_domain_access('finance', 'user-1'))

  assert exc.value.status_code == 403
  assert exc.value.detail == 'Domain access not configured'


def test_check_domain_access_rejects_missing_role(monkeypatch):
  auth = AuthModule(FastAPI())
  auth.domain_role_map = {'finance': 0x10}

  async def _deny(_guid: str, _mask: int) -> bool:
    return False

  monkeypatch.setattr(auth, 'user_has_role', _deny)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(auth.check_domain_access('finance', 'user-1'))

  assert exc.value.status_code == 403
  assert exc.value.detail == 'Forbidden'


def test_check_domain_access_allows_role(monkeypatch):
  auth = AuthModule(FastAPI())
  auth.domain_role_map = {'finance': 0x10}

  async def _allow(_guid: str, _mask: int) -> bool:
    return True

  monkeypatch.setattr(auth, 'user_has_role', _allow)

  asyncio.run(auth.check_domain_access('finance', 'user-1'))

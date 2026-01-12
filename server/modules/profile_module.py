"""Profile module wrapping account profile registry helpers."""

from __future__ import annotations

from fastapi import FastAPI

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule
from server.registry.account.profile.model import (
  GuidParams,
  ProfileRecord,
  SetDisplayParams,
  SetOptInParams,
  SetProfileImageParams,
)
from server.modules.registry.helpers import (
  get_profile_request,
  set_display_request,
  set_optin_request,
  set_profile_image_request,
)


class ProfileModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.auth: AuthModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.auth = self.app.state.auth
    await self.auth.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self.auth = None

  async def get_profile(self, guid: str) -> ProfileRecord | None:
    assert self.db
    params = GuidParams(guid=guid)
    res = await self.db.run(get_profile_request(params))
    return res.rows[0] if res.rows else None

  async def set_display(self, guid: str, display_name: str) -> None:
    assert self.db
    params = SetDisplayParams(guid=guid, display_name=display_name)
    await self.db.run(set_display_request(params))

  async def set_optin(self, guid: str, display_email: bool) -> None:
    assert self.db
    params = SetOptInParams(guid=guid, display_email=display_email)
    await self.db.run(set_optin_request(params))

  async def get_roles(self, guid: str) -> int:
    assert self.auth
    _, mask = await self.auth.get_user_roles(guid)
    return mask

  async def set_profile_image(self, guid: str, provider: str, image_b64: str | None) -> None:
    assert self.db
    params = SetProfileImageParams(guid=guid, provider=provider, image_b64=image_b64)
    await self.db.run(set_profile_image_request(params))

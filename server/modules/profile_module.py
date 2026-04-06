"""Profile module wrapping account profile registry helpers."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule
from queryregistry.identity.profiles import get_profile_request, update_profile_request
from queryregistry.identity.profiles.models import (
  GuidParams,
  ProfileRecord,
  UpdateProfileParams,
)


class UsersProfileProfile1(BaseModel):
  guid: str
  display_name: str
  email: str
  display_email: bool
  credits: int
  profile_image: str | None = None
  default_provider: str
  auth_providers: list[dict]


class UsersProfileRoles1(BaseModel):
  roles: int


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


  async def get_profile(self, guid: str) -> UsersProfileProfile1:
    params = GuidParams(guid=guid)
    res = await self.db.run(get_profile_request(params))
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")

    record: ProfileRecord = res.rows[0]
    auth_providers = record.get("auth_providers")
    if auth_providers is None:
      normalized_auth_providers = []
    elif isinstance(auth_providers, list):
      normalized_auth_providers = auth_providers
    else:
      raise HTTPException(status_code=500, detail="Invalid auth provider payload")

    return UsersProfileProfile1(
      guid=str(record.get("guid", "")),
      display_name=record.get("display_name") or "",
      email=record.get("email") or "",
      display_email=bool(record.get("display_email", False)),
      credits=int(record.get("credits", 0) or 0),
      profile_image=record.get("profile_image"),
      default_provider=record.get("default_provider") or "",
      auth_providers=normalized_auth_providers,
    )

  async def set_display(self, guid: str, display_name: str) -> None:
    params = UpdateProfileParams(guid=guid, display_name=display_name)
    await self.db.run(update_profile_request(params))

  async def set_optin(self, guid: str, display_email: bool) -> None:
    params = UpdateProfileParams(guid=guid, display_email=display_email)
    await self.db.run(update_profile_request(params))

  async def get_roles(self, guid: str) -> UsersProfileRoles1:
    assert self.auth
    _, mask = await self.auth.get_user_roles(guid)
    return UsersProfileRoles1(roles=mask)

  async def set_profile_image(self, guid: str, provider: str, image_b64: str | None) -> None:
    params = UpdateProfileParams(guid=guid, provider=provider, image_b64=image_b64)
    await self.db.run(update_profile_request(params))

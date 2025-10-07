from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException

from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.registry.users.content.profile import (
  get_profile_request,
  set_display_request,
  set_optin_request,
  set_profile_image_request,
)
from server.registry.users.security.accounts import get_security_profile_request
from rpc.users.profile.models import (
  UsersProfileProfile1,
  UsersProfileRoles1,
)


class UserProfileModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def get_profile(self, guid: str) -> UsersProfileProfile1:
    assert self.db, "database module not initialised"
    request = get_profile_request(guid=guid)
    res = await self.db.run(request)
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = dict(res.rows[0])
    row["guid"] = str(row.get("guid") or row.get("user_guid") or "")
    auth_providers = row.get("auth_providers")
    if isinstance(auth_providers, str):
      row["auth_providers"] = json.loads(auth_providers) if auth_providers else []
    elif auth_providers is None:
      row["auth_providers"] = []
    return UsersProfileProfile1(**row)

  async def set_display(self, guid: str, display_name: str) -> None:
    assert self.db, "database module not initialised"
    request = set_display_request(guid=guid, display_name=display_name)
    await self.db.run(request)

  async def set_optin(self, guid: str, display_email: bool) -> None:
    assert self.db, "database module not initialised"
    request = set_optin_request(guid=guid, display_email=display_email)
    await self.db.run(request)

  async def get_roles(self, guid: str) -> UsersProfileRoles1:
    assert self.db, "database module not initialised"
    request = get_security_profile_request(guid=guid)
    res = await self.db.run(request)
    row = res.rows[0] if res.rows else {}
    roles = int(row.get("user_roles") or row.get("element_roles") or 0)
    return UsersProfileRoles1(roles=roles)

  async def set_profile_image(self, guid: str, image_b64: str, provider: str) -> None:
    assert self.db, "database module not initialised"
    request = set_profile_image_request(guid=guid, image_b64=image_b64, provider=provider)
    await self.db.run(request)

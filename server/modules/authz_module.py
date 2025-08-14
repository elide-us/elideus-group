import logging
from typing import Dict

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule

ROLES: Dict[str, int] = {}
ROLE_NAMES: list[str] = []
ROLE_REGISTERED: int = 1

class AuthzModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    await self.load_roles()
    logging.info("AuthzModule loaded %d roles", len(ROLES))
    self.mark_ready()

  async def shutdown(self):
    logging.info("AuthzModule shutdown")

  async def load_roles(self):
    if not self.db:
      return
    try:
      result = await self.db.run("db:system:roles:list:1", {})
    except Exception:
      return
    rows = result.rows
    if not rows:
      return
    ROLES.clear()
    for r in rows:
      ROLES[r['name']] = int(r['mask'])
    global ROLE_NAMES, ROLE_REGISTERED
    ROLE_NAMES = [n for n in ROLES.keys() if n != 'ROLE_REGISTERED']
    ROLE_REGISTERED = ROLES.get('ROLE_REGISTERED', 0)

  def mask_to_names(self, mask: int) -> list[str]:
    return [name for name, bit in ROLES.items() if mask & bit]

  def names_to_mask(self, names: list[str]) -> int:
    mask = 0
    for name in names:
      mask |= ROLES.get(name, 0)
    return mask

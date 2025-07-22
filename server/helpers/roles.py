# The role bitmasks must fit in a signed 64-bit integer as they are stored using
# the Postgres ``BIGINT`` type. Using ``0x8000000000000000`` would flip the sign
# bit, so the highest role begins at ``0x4000000000000000`` and the remaining
# roles shift down from there.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from server.modules.database_module import DatabaseModule

ROLE_DEFAULTS = {
  'ROLE_SERVICE_ADMIN': 0x4000000000000000,
  'ROLE_SYSTEM_ADMIN': 0x2000000000000000,
  'ROLE_MODERATOR': 0x0800000000000000,
  'ROLE_SUPPORT': 0x0400000000000000,
  'ROLE_REGISTERED': 0x0000000000000001,
}

ROLES = ROLE_DEFAULTS.copy()

ROLE_SERVICE_ADMIN = ROLES['ROLE_SERVICE_ADMIN']
ROLE_SYSTEM_ADMIN = ROLES['ROLE_SYSTEM_ADMIN']
ROLE_MODERATOR = ROLES['ROLE_MODERATOR']
ROLE_SUPPORT = ROLES['ROLE_SUPPORT']
ROLE_REGISTERED = ROLES['ROLE_REGISTERED']

ROLE_NAMES = [name for name in ROLES.keys() if name != 'ROLE_REGISTERED']

def _refresh_globals():
  globals().update({
    'ROLE_SERVICE_ADMIN': ROLES.get('ROLE_SERVICE_ADMIN', 0),
    'ROLE_SYSTEM_ADMIN': ROLES.get('ROLE_SYSTEM_ADMIN', 0),
    'ROLE_MODERATOR': ROLES.get('ROLE_MODERATOR', 0),
    'ROLE_SUPPORT': ROLES.get('ROLE_SUPPORT', 0),
    'ROLE_REGISTERED': ROLES.get('ROLE_REGISTERED', 0),
    'ROLE_NAMES': [n for n in ROLES.keys() if n != 'ROLE_REGISTERED'],
  })

def mask_to_names(mask: int) -> list[str]:
  return [name for name, bit in ROLES.items() if mask & bit]

def names_to_mask(names: list[str]) -> int:
  mask = 0
  for name in names:
    mask |= ROLES.get(name, 0)
  return mask

async def load_from_db(db: 'DatabaseModule') -> None:
  rows = await db._fetch_many('SELECT name, mask FROM roles;')
  if rows:
    ROLES.clear()
    for r in rows:
      ROLES[r['name']] = int(r['mask'])
    _refresh_globals()

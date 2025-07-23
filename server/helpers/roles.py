# Mapping of role names to their masks loaded from the database.
ROLES: dict[str, int] = {}

# List of all roles except ``ROLE_REGISTERED`` for convenience.
ROLE_NAMES: list[str] = []

# ``ROLE_REGISTERED`` is used frequently so expose it directly.  It will be
# updated when ``load_roles`` is called.  Default to ``1`` so code using the
# constant before roles are loaded behaves as expected.
ROLE_REGISTERED: int = 1

async def load_roles(db) -> None:
  rows = await db.list_roles()
  if not rows:
    return
  ROLES.clear()
  for r in rows:
    ROLES[r['name']] = int(r['mask'])
  global ROLE_NAMES, ROLE_REGISTERED
  ROLE_NAMES = [n for n in ROLES.keys() if n != 'ROLE_REGISTERED']
  ROLE_REGISTERED = ROLES.get('ROLE_REGISTERED', 0)

def mask_to_names(mask: int) -> list[str]:
  return [name for name, bit in ROLES.items() if mask & bit]

def names_to_mask(names: list[str]) -> int:
  mask = 0
  for name in names:
    mask |= ROLES.get(name, 0)
  return mask

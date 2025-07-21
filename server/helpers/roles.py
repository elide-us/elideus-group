# The role bitmasks must fit in a signed 64-bit integer as they are stored using
# the Postgres ``BIGINT`` type. Using ``0x8000000000000000`` would flip the sign
# bit, so the highest role begins at ``0x4000000000000000`` and the remaining
# roles shift down from there.
ROLE_SERVICE_ADMIN = 0x4000000000000000
ROLE_SYSTEM_ADMIN = 0x2000000000000000
ROLE_MODERATOR = 0x0800000000000000
ROLE_SUPPORT = 0x0400000000000000
ROLE_REGISTERED = 0x0000000000000001

ROLES = {
  'ROLE_SERVICE_ADMIN': ROLE_SERVICE_ADMIN,
  'ROLE_SYSTEM_ADMIN': ROLE_SYSTEM_ADMIN,
  'ROLE_MODERATOR': ROLE_MODERATOR,
  'ROLE_SUPPORT': ROLE_SUPPORT,
  'ROLE_REGISTERED': ROLE_REGISTERED,
}

ROLE_NAMES = [name for name in ROLES.keys() if name != 'ROLE_REGISTERED']

def mask_to_names(mask: int) -> list[str]:
  return [name for name, bit in ROLES.items() if mask & bit]

def names_to_mask(names: list[str]) -> int:
  mask = 0
  for name in names:
    mask |= ROLES.get(name, 0)
  return mask

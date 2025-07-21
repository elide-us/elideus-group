ROLE_SERVICE_ADMIN = 0x8000000000000000
ROLE_SYSTEM_ADMIN = 0x4000000000000000
ROLE_MODERATOR = 0x2000000000000000
ROLE_SUPPORT = 0x1000000000000000

ROLES = {
  'ROLE_SERVICE_ADMIN': ROLE_SERVICE_ADMIN,
  'ROLE_SYSTEM_ADMIN': ROLE_SYSTEM_ADMIN,
  'ROLE_MODERATOR': ROLE_MODERATOR,
  'ROLE_SUPPORT': ROLE_SUPPORT,
}

ROLE_NAMES = list(ROLES.keys())

def mask_to_names(mask: int) -> list[str]:
  return [name for name, bit in ROLES.items() if mask & bit]

def names_to_mask(names: list[str]) -> int:
  mask = 0
  for name in names:
    mask |= ROLES.get(name, 0)
  return mask

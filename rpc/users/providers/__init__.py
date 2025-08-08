"""Users providers RPC namespace.

Manage authentication providers for a user. Requires
ROLE_USERS_ENABLED.
"""

from .services import (
  users_providers_set_provider_v1,
  users_providers_link_provider_v1,
  users_providers_unlink_provider_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("set_provider", "1"): users_providers_set_provider_v1,
  ("link_provider", "1"): users_providers_link_provider_v1,
  ("unlink_provider", "1"): users_providers_unlink_provider_v1,
}


"""Users auth RPC namespace.

Unauthenticated; no role required.
"""

from .services import (users_auth_set_provider_v1,
                       users_auth_link_provider_v1,
                       users_auth_unlink_provider_v1)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("set_provider", "1"): users_auth_set_provider_v1,
  ("link_provider", "1"): users_auth_link_provider_v1,
  ("unlink_provider", "1"): users_auth_unlink_provider_v1
}


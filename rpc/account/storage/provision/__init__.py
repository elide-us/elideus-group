"""Account storage provision RPC namespace."""

from .services import (
  storage_provision_create_user_v1,
  storage_provision_check_user_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("create_user", "1"): storage_provision_create_user_v1,
  ("check_user", "1"): storage_provision_check_user_v1,
}

from .services import auth_providers_unlink_last_provider_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("unlink_last_provider", "1"): auth_providers_unlink_last_provider_v1,
}

from .services import (
  system_config_delete_config_v1,
  system_config_get_configs_v1,
  system_config_upsert_config_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  """
    These functions are used to make changes to the system configuration.
    These values are stored in the database.
    This namespace is restricted to only users with the SYSTEM role.
  """
  ("get_configs", "1"): system_config_get_configs_v1,
  ("upsert_config", "1"): system_config_upsert_config_v1,
  ("delete_config", "1"): system_config_delete_config_v1
}


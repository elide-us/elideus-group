from .services import (system_config_delete_config_v1,
                       system_config_get_configs_v1,
                       system_config_set_config_v1)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_configs", "1"): system_config_get_configs_v1,
  ("set_config", "1"): system_config_set_config_v1,
  ("delete_config", "1"): system_config_delete_config_v1
}


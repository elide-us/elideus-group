from .services import (
    list_config_v1,
    set_config_v1,
    delete_config_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): list_config_v1,
  ("set", "1"): set_config_v1,
  ("delete", "1"): delete_config_v1
}

from .services import get_profile_data_v1, set_display_name_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile_data", "1"): get_profile_data_v1,
  ("set_display_name", "1"): set_display_name_v1,
}

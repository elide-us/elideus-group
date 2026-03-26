from .services import public_pages_get_page_v1, public_pages_list_pages_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_pages", "1"): public_pages_list_pages_v1,
  ("get_page", "1"): public_pages_get_page_v1,
}

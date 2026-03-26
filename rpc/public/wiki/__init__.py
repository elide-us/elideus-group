from .services import public_wiki_get_page_v1, public_wiki_list_pages_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_pages", "1"): public_wiki_list_pages_v1,
  ("get_page", "1"): public_wiki_get_page_v1,
}

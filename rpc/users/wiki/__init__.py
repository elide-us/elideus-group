from .services import users_wiki_create_version_v1, users_wiki_get_version_v1, users_wiki_list_versions_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("create_version", "1"): users_wiki_create_version_v1,
  ("list_versions", "1"): users_wiki_list_versions_v1,
  ("get_version", "1"): users_wiki_get_version_v1,
}

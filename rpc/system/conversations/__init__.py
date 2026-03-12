from .services import (
  system_conversations_delete_before_v1,
  system_conversations_delete_thread_v1,
  system_conversations_list_v1,
  system_conversations_stats_v1,
  system_conversations_view_thread_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_conversations", "1"): system_conversations_list_v1,
  ("get_stats", "1"): system_conversations_stats_v1,
  ("view_thread", "1"): system_conversations_view_thread_v1,
  ("delete_thread", "1"): system_conversations_delete_thread_v1,
  ("delete_before", "1"): system_conversations_delete_before_v1,
}

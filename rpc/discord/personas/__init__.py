"""Discord personas RPC namespace.

Handlers are dispatched by :mod:`rpc.discord.handler` after role checks for
``ROLE_DISCORD_ADMIN`` succeed.
"""

from .services import (
  discord_personas_delete_persona_v1,
  discord_personas_get_models_v1,
  discord_personas_get_personas_v1,
  discord_personas_upsert_persona_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_personas", "1"): discord_personas_get_personas_v1,
  ("get_models", "1"): discord_personas_get_models_v1,
  ("upsert_persona", "1"): discord_personas_upsert_persona_v1,
  ("delete_persona", "1"): discord_personas_delete_persona_v1,
}

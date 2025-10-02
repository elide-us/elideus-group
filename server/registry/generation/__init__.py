"""Generation domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.assistant import conversations, models, personas

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "conversations",
  "models",
  "personas",
  "register",
]


def register(router: "RegistryRouter") -> None:
  domain = router.domain("assistant")
  conversations.register(domain.subdomain("conversations"))
  models.register(domain.subdomain("models"))
  personas.register(domain.subdomain("personas"))

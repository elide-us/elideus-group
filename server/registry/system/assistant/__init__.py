"""Assistant registry bindings for the system domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import conversations, models, personas

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "conversations",
  "models",
  "personas",
  "register",
]


def register(domain: "DomainRouter") -> None:
  conversations.register(domain.subdomain("assistant.conversations"))
  models.register(domain.subdomain("assistant.models"))
  personas.register(domain.subdomain("assistant.personas"))

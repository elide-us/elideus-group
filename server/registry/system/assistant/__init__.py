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
  assistant_router = domain.subdomain("assistant")
  conversations.register(assistant_router.subdomain("conversations"))
  models.register(assistant_router.subdomain("models"))
  personas.register(assistant_router.subdomain("personas"))

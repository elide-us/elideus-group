"""Discord registry bindings for the system domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import guilds

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "guilds",
  "register",
]


def register(domain: "DomainRouter") -> None:
  discord_router = domain.subdomain("discord")
  guilds.register(discord_router.subdomain("guilds"))

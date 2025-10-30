"""Finance domain registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import credits

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "credits",
  "register",
]


def register(router: "RegistryRouter") -> None:
  credits.register(router, domain="finance", path=("credits",))

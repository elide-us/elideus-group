"""Public registry bindings for the system domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import vars as _vars

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "register",
  "vars",
]

vars = _vars


def register(domain: "DomainRouter") -> None:
  vars.register(domain.subdomain("public.vars"))

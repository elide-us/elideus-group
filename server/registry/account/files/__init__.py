"""Account files registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "set_gallery_request",
  "register",
]


def set_gallery_request(user_guid: str, name: str, gallery: bool) -> DBRequest:
  return DBRequest(
    op="db:account:files:set_gallery:1",
    payload={
      "user_guid": user_guid,
      "name": name,
      "gallery": bool(gallery),
    },
  )


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="set_gallery", version=1)

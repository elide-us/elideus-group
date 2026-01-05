"""Account files registry helpers."""

from __future__ import annotations

from server.registry.types import DBRequest



def set_gallery_request(user_guid: str, name: str, gallery: bool) -> DBRequest:
  return DBRequest(
    op="db:account:files:set_gallery:1",
    payload={
      "user_guid": user_guid,
      "name": name,
      "gallery": bool(gallery),
    },
  )

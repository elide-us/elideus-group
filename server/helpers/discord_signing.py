"""Shared helpers for Discord request signing."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping

_SEPARATORS: tuple[str, str] = (',', ':')


def _normalise(value: Any | None) -> str:
  if value is None:
    return ''
  return str(value)


def canonicalise_body(body: Mapping[str, Any]) -> str:
  """Return a deterministic JSON representation for signing."""

  return json.dumps(body, separators=_SEPARATORS, sort_keys=True, ensure_ascii=False)


def build_signature_message(
  body: Mapping[str, Any],
  *,
  timestamp: str,
  user_id: Any | None = None,
  guild_id: Any | None = None,
  channel_id: Any | None = None,
) -> str:
  """Build the canonical signing payload for Discord ingress requests."""

  serialized_body = canonicalise_body(body)
  components = [
    str(timestamp),
    serialized_body,
    _normalise(user_id),
    _normalise(guild_id),
    _normalise(channel_id),
  ]
  return "\n".join(components)


def compute_signature(
  secret: str,
  *,
  body: Mapping[str, Any],
  timestamp: str,
  user_id: Any | None = None,
  guild_id: Any | None = None,
  channel_id: Any | None = None,
) -> str:
  """Compute the Discord ingress HMAC signature."""

  message = build_signature_message(
    body,
    timestamp=timestamp,
    user_id=user_id,
    guild_id=guild_id,
    channel_id=channel_id,
  )
  digest = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
  return digest.hexdigest()


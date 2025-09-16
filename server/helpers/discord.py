import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

__all__ = [
  "send_to_discord",
  "send_to_discord_user",
]


class _SupportsSend(Protocol):
  async def send(self, message: str) -> None: ...


_SendCallable = Callable[[str], Awaitable[None]]


async def _chunked_send(
  send: _SendCallable,
  text: str,
  max_message_size: int = 1998,
  delay: float = 1.0,
) -> None:
  """Split ``text`` into Discord-safe messages and send them sequentially."""

  for block in text.split("\n"):
    if not block.strip() or block.strip() == "---":
      continue

    start = 0
    while start < len(block):
      end = min(start + max_message_size, len(block))

      if end < len(block) and block[end] != " ":
        adjusted_end = block.rfind(" ", start, end)
        if adjusted_end == -1 or adjusted_end <= start:
          adjusted_end = min(start + max_message_size, len(block))
        end = adjusted_end

      if end <= start:
        end = min(start + max_message_size, len(block))
        if end <= start:
          break

      chunk = block[start:end].strip()
      if chunk:
        await send(chunk)
        if delay > 0:
          await asyncio.sleep(delay)

      start = end


async def send_to_discord(
  channel: _SupportsSend,
  text: str,
  max_message_size: int = 1998,
  delay: float = 1.0,
) -> None:
  await _chunked_send(channel.send, text, max_message_size, delay)


async def send_to_discord_user(
  user: _SupportsSend,
  text: str,
  max_message_size: int = 1998,
  delay: float = 1.0,
) -> None:
  await _chunked_send(user.send, text, max_message_size, delay)

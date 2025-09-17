import asyncio
from collections.abc import Awaitable, Callable
from typing import List, Protocol

__all__ = [
  "send_to_discord",
  "send_to_discord_user",
]


class _SupportsSend(Protocol):
  async def send(self, message: str) -> None: ...


_SendCallable = Callable[[str], Awaitable[None]]


def _wrap_line(line: str, max_message_size: int) -> List[str]:
  """Split a single line into message-sized chunks."""

  remaining = line
  parts: List[str] = []

  while remaining:
    if len(remaining) <= max_message_size:
      parts.append(remaining)
      break

    window = remaining[:max_message_size]
    split = window.rfind(" ")
    if split <= 0:
      split = max_message_size

    parts.append(remaining[:split])
    remaining = remaining[split:]

  if not parts:
    parts.append("")

  return parts


def _yield_chunks(text: str, max_message_size: int) -> List[str]:
  """Yield message-sized chunks preserving multi-line formatting."""

  normalized = text.replace("\r\n", "\n").replace("\r", "\n")
  lines = normalized.split("\n")
  chunks: List[str] = []
  buffer = ""

  for raw_line in lines:
    line = raw_line
    if not line.strip() and not buffer.strip():
      continue

    wrapped = _wrap_line(line, max_message_size)
    for segment in wrapped[:-1]:
      candidate = segment if not buffer else buffer + "\n" + segment
      if candidate.strip() and candidate.strip() != "---":
        chunks.append(candidate)
      buffer = ""

    last_segment = wrapped[-1]
    candidate = last_segment if not buffer else buffer + ("\n" + last_segment if last_segment else "\n")

    if len(candidate) <= max_message_size:
      buffer = candidate
    else:
      if buffer.strip() and buffer.strip() != "---":
        chunks.append(buffer)
      buffer = last_segment

  if buffer.strip() and buffer.strip() != "---":
    chunks.append(buffer)

  return chunks


async def _chunked_send(
  send: _SendCallable,
  text: str,
  max_message_size: int = 1998,
  delay: float = 1.0,
) -> None:
  """Split ``text`` into Discord-safe messages and send them sequentially."""

  for chunk in _yield_chunks(text, max_message_size):
    await send(chunk)
    if delay > 0:
      await asyncio.sleep(delay)


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

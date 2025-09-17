import asyncio
from fastapi import FastAPI

from server.modules.discord_output_module import DiscordOutputModule


class DummySender:
  def __init__(self):
    self.sent: list[str] = []

  async def send(self, message: str) -> None:
    self.sent.append(message)


def _create_module(message_size: int) -> DiscordOutputModule:
  module = DiscordOutputModule(FastAPI())
  module.configure_message_window(message_size)
  module.configure_trickle_rate(0)
  return module


def test_send_to_discord_chunks_long_message():
  sender = DummySender()
  text = "A" * 4500
  module = _create_module(1000)

  async def run():
    await module._deliver_in_chunks(sender.send, text)

  asyncio.run(run())
  assert len(sender.sent) == 5
  assert "".join(sender.sent) == text


def test_send_to_discord_handles_multiline_text():
  sender = DummySender()
  text = "Intro paragraph." "\n\n" "---" "\n\n" + "Section " + "A" * 1200 + "\nConclusion line with trailing spaces  "
  module = _create_module(500)

  async def run():
    await module._deliver_in_chunks(sender.send, text)

  asyncio.run(run())

  assert all(len(chunk) <= 500 for chunk in sender.sent)
  compact_original = text.replace("\n", "")
  compact_sent = "".join(chunk.replace("\n", "") for chunk in sender.sent)
  assert compact_sent == compact_original
  newline_count_sent = sum(chunk.count("\n") for chunk in sender.sent)
  assert newline_count_sent == text.count("\n")

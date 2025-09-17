import asyncio

from server.helpers.discord import send_to_discord


class DummyChannel:
  def __init__(self):
    self.sent: list[str] = []

  async def send(self, message: str) -> None:
    self.sent.append(message)


def test_send_to_discord_chunks_long_message():
  channel = DummyChannel()
  text = "A" * 4500

  async def run():
    await send_to_discord(channel, text, max_message_size=1000, delay=0)

  asyncio.run(run())
  assert len(channel.sent) == 5
  assert "".join(channel.sent) == text


def test_send_to_discord_handles_multiline_text():
  channel = DummyChannel()
  text = "Intro paragraph." "\n\n" "---" "\n\n" + "Section " + "A" * 1200 + "\nConclusion line with trailing spaces  "

  async def run():
    await send_to_discord(channel, text, max_message_size=500, delay=0)

  asyncio.run(run())

  assert all(len(chunk) <= 500 for chunk in channel.sent)
  compact_original = text.replace("\n", "")
  compact_sent = "".join(chunk.replace("\n", "") for chunk in channel.sent)
  assert compact_sent == compact_original
  newline_count_sent = sum(chunk.count("\n") for chunk in channel.sent)
  assert newline_count_sent == text.count("\n")

import logging, asyncio
from types import SimpleNamespace
from server.helpers.logging import DiscordHandler, configure_discord_logging, remove_discord_logging


class DummyChannel:
  def __init__(self):
    self.messages = []
  async def send(self, msg):
    self.messages.append(msg)


class DummyLoop:
  def __init__(self):
    self.tasks = []
  def create_task(self, coro):
    self.tasks.append(coro)
    return coro


class DummyBot:
  def __init__(self, channel=None):
    self.loop = DummyLoop()
    self.channel = channel
  def get_channel(self, _):
    return self.channel


def _has_handler(discord):
  logger = logging.getLogger()
  for h in logger.handlers:
    if isinstance(h, DiscordHandler) and h.discord is discord:
      return True
  return False


def test_configure_logging_emits_message():
  channel = DummyChannel()
  bot = DummyBot(channel)
  discord = SimpleNamespace(bot=bot, syschan=1)
  configure_discord_logging(discord)
  logging.getLogger().setLevel(logging.INFO)
  logging.info("hello")
  assert len(bot.loop.tasks) == 1
  asyncio.run(bot.loop.tasks[0])
  assert channel.messages == ["[INFO] hello"]
  remove_discord_logging(discord)


def test_remove_discord_logging():
  bot = DummyBot(DummyChannel())
  discord = SimpleNamespace(bot=bot, syschan=1)
  configure_discord_logging(discord)
  assert _has_handler(discord)
  remove_discord_logging(discord)
  assert not _has_handler(discord)


def test_emit_without_channel():
  bot = DummyBot(None)
  discord = SimpleNamespace(bot=bot, syschan=1)
  configure_discord_logging(discord)
  logging.getLogger().setLevel(logging.INFO)
  logging.info("msg")
  assert bot.loop.tasks == []
  remove_discord_logging(discord)


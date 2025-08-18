import logging, asyncio, time
import sys

MAX_DISCORD_MESSAGE_LEN = 1900

def split_message(msg: str, limit: int = MAX_DISCORD_MESSAGE_LEN) -> list[str]:
  return [msg[i:i + limit] for i in range(0, len(msg), limit)]

class DiscordHandler(logging.Handler):
  def __init__(self, discord_module, interval: float = 1.0, delay: float = 5.0):
    super().__init__()
    self.discord = discord_module
    self.interval = interval
    self.delay = delay
    self.async_lock = asyncio.Lock()
    self.last_sent = 0.0

  def emit(self, record):
    if record.name.startswith('discord'):
      return

    msg = self.format(record)

    if not msg or msg == "None":
      return

    try:
      chan = self.discord.bot.get_channel(self.discord.syschan)
      if chan:
        self.discord.bot.loop.create_task(self._send(msg))
    except Exception:
      pass

  async def _send(self, msg: str):
    async with self.async_lock:
      now = time.monotonic()
      wait = self.interval - (now - self.last_sent)
      if wait > 0:
        await asyncio.sleep(wait)

      chan = self.discord.bot.get_channel(self.discord.syschan)
      if not chan:
        return

      for part in split_message(msg):
        try:
          await chan.send(part)
        except Exception as e:
          if getattr(e, 'status', None) == 429:
            await asyncio.sleep(self.delay)
            try:
              await chan.send('Discord logging rate limited, resuming.')
              await chan.send(part)
            except Exception:
              pass
        self.last_sent = time.monotonic()

def configure_discord_logging(discord_module):
  handler = DiscordHandler(discord_module)
  handler.setLevel(logging.INFO)
  handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
  logging.getLogger().addHandler(handler)
  logging.getLogger('discord').setLevel(logging.WARNING)
  logging.getLogger('discord.http').setLevel(logging.WARNING)

def update_logging_level(debug: bool = False):
  """Update global logging level including Azure SDK logger."""
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG if debug else logging.INFO)
  azure_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
  azure_logger.setLevel(logging.DEBUG if debug else logging.WARNING)

def configure_root_logging(debug: bool = False):
  logger = logging.getLogger()
  if logger.handlers:
    logger.handlers.clear()
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
  logger.addHandler(handler)
  update_logging_level(debug)

def remove_discord_logging(discord_module):
  logger = logging.getLogger()
  for h in list(logger.handlers):
    if isinstance(h, DiscordHandler) and h.discord is discord_module:
      logger.removeHandler(h)


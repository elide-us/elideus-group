import logging, asyncio, time
import sys

class DiscordHandler(logging.Handler):
  def __init__(self, discord_module, interval: float = 1.0, delay: float = 5.0):
    super().__init__()
    self.discord = discord_module
    self.interval = interval
    self.delay = delay
    self.async_lock = asyncio.Lock()
    self.last_sent = 0.0

  def emit(self, record):
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

      try:
        await chan.send(msg)
      except Exception as e:
        if getattr(e, 'status', None) == 429:
          await asyncio.sleep(self.delay)
          try:
            await chan.send('Discord logging rate limited, resuming.')
            await chan.send(msg)
          except Exception:
            pass
      self.last_sent = time.monotonic()

def configure_discord_logging(discord_module):
  handler = DiscordHandler(discord_module)
  handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
  logging.getLogger().addHandler(handler)


def configure_root_logging():
  logger = logging.getLogger()
  if logger.handlers:
    logger.handlers.clear()
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
  logger.addHandler(handler)
  logger.setLevel(logging.INFO)


def remove_discord_logging(discord_module):
  logger = logging.getLogger()
  for h in list(logger.handlers):
    if isinstance(h, DiscordHandler) and h.discord is discord_module:
      logger.removeHandler(h)

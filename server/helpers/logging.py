import logging, asyncio, time
import sys

MAX_DISCORD_MESSAGE_LEN = 1900

_logger = logging.getLogger(__name__)

def split_message(msg: str, limit: int = MAX_DISCORD_MESSAGE_LEN) -> list[str]:
  return [msg[i:i + limit] for i in range(0, len(msg), limit)]

class ExcludeDiscordFilter(logging.Filter):
  def filter(self, record):
    return not record.name.startswith('discord')

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
    except Exception:
      _logger.warning("Discord logging channel lookup failed", exc_info=True)
      return

    if not chan:
      _logger.debug("Discord logging channel %s unavailable", getattr(self.discord, 'syschan', 'unknown'))
      return

    try:
      self.discord.bot.loop.create_task(self._send(msg))
    except Exception:
      _logger.warning("Discord logging queue dispatch failed", exc_info=True)

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
        except Exception as exc:
          if getattr(exc, 'status', None) == 429:
            _logger.warning("Discord logging rate limited; retrying", exc_info=True)
            await asyncio.sleep(self.delay)
            try:
              await chan.send('Discord logging rate limited, resuming.')
              await chan.send(part)
            except Exception as retry_exc:
              _logger.warning("Discord logging retry failed", exc_info=retry_exc)
              return
          else:
            _logger.warning("Discord logging send failed", exc_info=exc)
            return
        self.last_sent = time.monotonic()

def configure_discord_logging(discord_module):
  handler = DiscordHandler(discord_module)
  handler.setLevel(logging.INFO)
  handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
  logging.getLogger().addHandler(handler)
  for name in ('discord', 'discord.http', 'discord.client', 'discord.gateway'):
    logging.getLogger(name).setLevel(logging.WARNING)

def update_logging_level(level: int = 3):
  """Update global logging level including Azure SDK logger.

  ``level`` mapping:
    0 → no logging
    1 → errors
    2 → errors and warnings
    3 → errors, warnings and info
    ≥4 → errors, warnings, info and debug

  Azure HTTP request/response logging is suppressed unless ``level >= 4``.
  """
  logger = logging.getLogger()
  logger.disabled = level <= 0
  if level <= 0:
    log_level = logging.CRITICAL + 1
  elif level == 1:
    log_level = logging.ERROR
  elif level == 2:
    log_level = logging.WARNING
  elif level == 3:
    log_level = logging.INFO
  else:
    log_level = logging.DEBUG
  logger.setLevel(log_level)

  # Azure's HTTP policy logs request/response details at INFO.
  # Only enable these verbose logs in debug mode.
  azure_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
  azure_logger.disabled = level <= 0
  if level >= 4:
    azure_level = logging.INFO
  elif level == 3:
    azure_level = logging.WARNING
  else:
    azure_level = logging.ERROR
  azure_logger.setLevel(azure_level)

def configure_root_logging(level: int = 3):
  logger = logging.getLogger()
  if logger.handlers:
    logger.handlers.clear()
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
  logger.addHandler(handler)
  logger.addFilter(ExcludeDiscordFilter())
  for name in ('discord', 'discord.http', 'discord.client', 'discord.gateway'):
    logging.getLogger(name).setLevel(logging.WARNING)
  update_logging_level(level)

def remove_discord_logging(discord_module):
  logger = logging.getLogger()
  for h in list(logger.handlers):
    if isinstance(h, DiscordHandler) and h.discord is discord_module:
      logger.removeHandler(h)


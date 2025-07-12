import logging

class DiscordHandler(logging.Handler):
  def __init__(self, discord_module):
    super().__init__()
    self.discord = discord_module

  def emit(self, record):
    msg = self.format(record)

    if not msg or msg == "None":
      return

    try:
      chan = self.discord.bot.get_channel(self.discord.syschan)
      if chan:
        self.discord.bot.loop.create_task(chan.send(msg)) # Dispatch async task in sync method
    except Exception:
      pass

def configure_discord_logging(discord_module):
  handler = DiscordHandler(discord_module)
  handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
  logging.getLogger().addHandler(handler)


def remove_discord_logging(discord_module):
  logger = logging.getLogger()
  for h in list(logger.handlers):
    if isinstance(h, DiscordHandler) and h.discord is discord_module:
      logger.removeHandler(h)

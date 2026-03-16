import asyncio
import logging
import sys

from server.helpers.error_digest import ErrorDigest
from server.helpers.logging import ConsoleDigestFormatter, DiscordHandler


def _raise_runtime_error_with_long_message():
  long_message = 'x' * 250
  raise RuntimeError(long_message)


def _raise_value_error():
  raise ValueError('digest me')


def test_error_digest_from_exception_filters_our_frames():
  try:
    _raise_value_error()
  except ValueError as exc:
    digest = ErrorDigest.from_exception(exc)

  assert digest.exception_type == 'ValueError'
  assert digest.origin_file.endswith('test_error_digest.py')
  assert digest.origin_function == '_raise_value_error'
  assert digest.origin_line > 0
  assert digest.our_frames
  assert len(digest.our_frames) <= 3
  assert any('/tests/' in frame.replace('\\', '/') for frame in digest.our_frames)
  assert 'Traceback (most recent call last)' in digest.full_traceback


def test_error_digest_short_and_detail_formatting():
  try:
    _raise_runtime_error_with_long_message()
  except RuntimeError as exc:
    digest = ErrorDigest.from_exception(exc)

  short = digest.short
  detail = digest.detail

  assert short.startswith('[RuntimeError] test_error_digest.py:')
  assert ' in _raise_runtime_error_with_long_message — ' in short
  assert short.endswith('...')
  assert len(short.split(' — ', 1)[1]) <= 200
  assert detail.startswith(short)
  assert '  → ' in detail


class _DummyChannel:
  def __init__(self):
    self.sent_messages = []

  async def send(self, message):
    self.sent_messages.append(message)


class _DummyLoop:
  def create_task(self, coro):
    asyncio.run(coro)


class _DummyBot:
  def __init__(self, channel):
    self._channel = channel
    self.loop = _DummyLoop()

  def get_channel(self, _):
    return self._channel


class _DummyDiscordModule:
  def __init__(self, channel):
    self.syschan = 42
    self.bot = _DummyBot(channel)


def test_discord_handler_emits_digest_short_for_exceptions():
  channel = _DummyChannel()
  handler = DiscordHandler(_DummyDiscordModule(channel), interval=0, delay=0)
  handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

  logger = logging.getLogger('test.discord.digest')

  try:
    _raise_value_error()
  except ValueError:
    record = logger.makeRecord(
      logger.name,
      logging.ERROR,
      __file__,
      0,
      'failed to process request',
      (),
      exc_info=sys.exc_info(),
    )

  handler.emit(record)

  assert channel.sent_messages
  message = channel.sent_messages[0]
  assert message.startswith('[ERROR] [ValueError] test_error_digest.py:')
  assert 'digest me' in message
  assert 'Traceback (most recent call last)' not in message


def test_console_digest_formatter_uses_detail_for_exception_text():
  formatter = ConsoleDigestFormatter('%(levelname)s: %(message)s')
  logger = logging.getLogger('test.console.digest')

  try:
    _raise_value_error()
  except ValueError:
    record = logger.makeRecord(
      logger.name,
      logging.ERROR,
      __file__,
      0,
      'failed in formatter',
      (),
      exc_info=sys.exc_info(),
    )

  output = formatter.format(record)
  assert 'ERROR: failed in formatter' in output
  assert '[ValueError] test_error_digest.py:' in output
  assert '  → ' in output

import aiohttp, io

# ###REVIEW### This helper is only used in tests and is not
# referenced by the application runtime.
class AsyncBufferWriter():
  def __init__(self, source):
    self.buffer = None
    self.source = source

  async def __aenter__(self):
    if isinstance(self.source, (bytes, bytearray)):
      self.buffer = io.BytesIO(self.source)
    else:
      self.buffer = await self._fetch_buffer()
    return self.buffer
  
  async def _fetch_buffer(self):
    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(self.source) as response:
          response.raise_for_status()
          return io.BytesIO(await response.read())
    except aiohttp.ClientError as e:
      raise ValueError(f"Failed to fetch buffer from {self.source}: {str(e)}")

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    if self.buffer:
      self.buffer.close()


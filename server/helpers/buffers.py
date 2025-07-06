import aiohttp, io

# Async Context Manager for buffer
class AsyncBufferWriter():
  def __init__(self, url):
    self.buffer = None
    self.url = url

  async def __aenter__(self):
    self.buffer = await self._fetch_buffer()
    return self.buffer
  
  async def _fetch_buffer(self):
    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(self.url) as response:
          response.raise_for_status()
          return io.BytesIO(await response.read())
    except aiohttp.ClientError as e:
      raise ValueError(f"Failed to fetch buffer from {self.url}: {str(e)}")

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    if self.buffer:
      self.buffer.close()
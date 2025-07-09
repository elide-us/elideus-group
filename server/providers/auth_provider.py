from fastapi import FastAPI
from . import Provider

class AuthProvider(Provider):
  def __init__(self, app: FastAPI):
    super().__init__(app)
  async def startup(self):
    pass
  async def shutdown(self):
    pass

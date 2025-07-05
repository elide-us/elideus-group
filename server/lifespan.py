from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.config import VERSION, HOSTNAME

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.version = VERSION
  app.state.hostname = HOSTNAME

  try:
    yield
  finally:
    return


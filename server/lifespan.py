from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.config import VERSION, HOSTNAME, REPO

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.version = VERSION
  app.state.hostname = HOSTNAME
  app.state.repo = REPO

  try:
    yield
  finally:
    return


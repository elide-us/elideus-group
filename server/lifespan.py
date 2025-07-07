from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.config import VERSION, HOSTNAME, REPO
from server.providers import ProviderRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.version = VERSION
  app.state.hostname = HOSTNAME
  app.state.repo = REPO

  registry = ProviderRegistry(app)
  app.state.providers = registry

  await registry.startup()

  try:
    yield
  finally:
    await registry.shutdown()

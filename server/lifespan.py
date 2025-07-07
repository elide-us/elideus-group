from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.providers import ProviderRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
  registry = ProviderRegistry(app)
  app.state.providers = registry

  await registry.startup()

  try:
    yield
  finally:
    await registry.shutdown()

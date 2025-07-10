from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.modules import ModuleRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
  registry = ModuleRegistry(app)
  app.state.modules = registry

  await registry.startup()

  try:
    yield
  finally:
    await registry.shutdown()

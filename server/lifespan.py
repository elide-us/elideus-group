from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.modules import ModuleManager

@asynccontextmanager
async def lifespan(app: FastAPI):
  manager = ModuleManager(app)
  await manager.startup_all()
  app.state.module_manager = manager

  try:
    yield
  finally:
    await manager.shutdown_all()


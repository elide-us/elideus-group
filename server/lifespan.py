from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.modules import ModuleManager
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
  manager = ModuleManager(app)
  await manager.startup_all()
  app.state.module_manager = manager

  from server.mcp_server import session_manager
  if session_manager is not None:
    async with session_manager.run():
      logging.info("[MCP] server mounted at /mcp")
      try:
        yield
      finally:
        await manager.shutdown_all()
  else:
    try:
      yield
    finally:
      await manager.shutdown_all()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.modules import ModuleManager
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
  manager = ModuleManager(app)
  await manager.startup_all()
  app.state.module_manager = manager

  mcp_module = getattr(app.state, "mcp_io_service", None)
  if mcp_module is not None and mcp_module.session_manager is not None:
    async with mcp_module.session_manager.run():
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

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from server.helpers.logging import configure_root_logging
from server.lifespan import lifespan
from server.mcp_server import init_session_manager, set_gateway_resolver
from server.routers import mcp_router, oauth_router, rpc_router, web_router

configure_root_logging(4)

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(rpc_router.router, prefix="/rpc")
app.include_router(oauth_router.router)
set_gateway_resolver(lambda: app.state.mcp_gateway)
init_session_manager()
app.include_router(mcp_router.router)
app.include_router(web_router.router)

@app.get("/")
async def get_root():
  return {"message": "If you are seeing this the React app is misconfigured."}

@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
  logging.exception("Unhandled exception")
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

################################################################################
## main.py - FastAPI server entry point module
##
## Creates the FastAPI server, configures the React app entry point,
## and configures route handlers.
################################################################################

# External imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from fastapi.staticfiles import StaticFiles

# Internal imports
from server import lifespan
from server.routers import rpc_router
from server.routers import web_router
from server.helpers.logging import configure_root_logging

configure_root_logging(debug=lifespan.DEBUG_LOGGING)

# Create the FastAPI app
app = FastAPI(lifespan=lifespan.lifespan)

# Configure the React app entry point
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure internal RPC router and React router pass-through
app.include_router(rpc_router.router, prefix="/rpc")
app.include_router(web_router.router)

# Configure default message in case of router failure
@app.get("/")
async def get_root():
  return {"message": "If you are seeing this the React app is misconfigured."}


@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
  logging.exception("Unhandled exception")
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

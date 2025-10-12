import logging
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from server import lifespan, rpc_router, web_router, configure_root_logging

configure_root_logging(4)

app = FastAPI(lifespan=lifespan.lifespan)
STATIC_URL_PREFIX: Final[str] = "/static"
app.mount(STATIC_URL_PREFIX, web_router.app)
app.include_router(rpc_router.router, prefix="/rpc")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index() -> Response:
  return await web_router.serve_index()


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_frontend(full_path: str) -> Response:
  return await web_router.serve_react_app(full_path)


@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
  logging.exception("Unhandled exception")
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

import logging
from typing import Final

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette import status
from server import lifespan, rpc_router, web_router, configure_root_logging

configure_root_logging(4)

app = FastAPI(lifespan=lifespan.lifespan)
STATIC_URL_PREFIX: Final[str] = "/static"
app.mount(STATIC_URL_PREFIX, web_router.app)
app.include_router(rpc_router.router, prefix="/rpc")


def _redirect_to_static(path: str = "") -> RedirectResponse:
  if path:
    target = f"{STATIC_URL_PREFIX}/{path}"
  else:
    target = f"{STATIC_URL_PREFIX}/"
  return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index() -> RedirectResponse:
  return _redirect_to_static()


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_static_routes(full_path: str) -> RedirectResponse:
  # Preserve API semantics for /rpc endpoints by falling through to the normal
  # routing logic instead of redirecting to the SPA.
  if full_path == "rpc" or full_path.startswith("rpc/"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
  return _redirect_to_static(full_path)


@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
  logging.exception("Unhandled exception")
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

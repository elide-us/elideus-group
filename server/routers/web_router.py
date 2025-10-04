from pathlib import Path
from typing import Final

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


STATIC_ROOT: Final[Path] = Path("static")
INDEX_FILE: Final[Path] = STATIC_ROOT / "index.html"
MAX_REQUEST_SIZE: Final[int] = 64 * 1024
ASSET_CACHE_CONTROL: Final[str] = "public, max-age=31536000, immutable"
HTML_CACHE_CONTROL: Final[str] = "no-cache, no-store, must-revalidate"
CSP_POLICY: Final[str] = (
  "default-src 'self'; "
  "script-src 'self' https://accounts.google.com; "
  "style-src 'self' 'unsafe-inline'; "
  "img-src 'self' data:; "
  "font-src 'self'; "
  "connect-src 'self' https://accounts.google.com; "
  "frame-ancestors 'none'; "
  "base-uri 'self'; "
  "form-action 'self'"
)


class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
  def __init__(self, app: ASGIApp, policy: str) -> None:
    super().__init__(app)
    self._policy = policy

  async def dispatch(self, request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Content-Security-Policy", self._policy)
    return response


class CacheControlMiddleware(BaseHTTPMiddleware):
  def __init__(
    self,
    app: ASGIApp,
    *,
    html_cache_control: str,
    asset_cache_control: str,
  ) -> None:
    super().__init__(app)
    self._html_cache_control = html_cache_control
    self._asset_cache_control = asset_cache_control

  async def dispatch(self, request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
      cache_control = self._html_cache_control
    else:
      cache_control = self._asset_cache_control
    response.headers["Cache-Control"] = cache_control
    return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
  def __init__(self, app: ASGIApp, *, max_request_size: int) -> None:
    super().__init__(app)
    self._max_request_size = max_request_size

  async def dispatch(self, request: Request, call_next):
    content_length_header = request.headers.get("content-length")
    if content_length_header:
      try:
        content_length = int(content_length_header)
      except ValueError:
        return Response(status_code=400)
      if content_length > self._max_request_size:
        return Response(status_code=413)

    if request.method in {"GET", "HEAD", "OPTIONS"}:
      return await call_next(request)

    return Response(status_code=405)


def _index_response() -> FileResponse:
  response = FileResponse(INDEX_FILE)
  response.headers["Cache-Control"] = HTML_CACHE_CONTROL
  return response


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(RequestSizeLimitMiddleware, max_request_size=MAX_REQUEST_SIZE)
app.add_middleware(ContentSecurityPolicyMiddleware, policy=CSP_POLICY)
app.add_middleware(
  CacheControlMiddleware,
  html_cache_control=HTML_CACHE_CONTROL,
  asset_cache_control=ASSET_CACHE_CONTROL,
)
app.mount("/assets", StaticFiles(directory=str(STATIC_ROOT / "assets")), name="static-assets")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index() -> FileResponse:
  return _index_response()


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_react_app(full_path: str) -> FileResponse:
  return _index_response()

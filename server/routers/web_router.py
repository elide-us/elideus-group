from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()

@router.get("/{full_path:path}")
async def serve_react_app(full_path: str):
  if full_path.startswith("mcp"):
    raise StarletteHTTPException(status_code=404)
  return FileResponse("static/index.html")

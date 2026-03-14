from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/{full_path:path}")
async def serve_react_app(full_path: str):
  if full_path.startswith("mcp/") or full_path.startswith(".well-known/"):
    raise HTTPException(status_code=404)
  return FileResponse("static/index.html")

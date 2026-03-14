from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/{full_path:path}")
async def serve_react_app(full_path: str):
  return FileResponse("static/index.html")

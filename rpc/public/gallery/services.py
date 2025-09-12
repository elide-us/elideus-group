from typing import TYPE_CHECKING
from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
if TYPE_CHECKING:
  from server.modules.public_gallery_module import PublicGalleryModule
from .models import PublicGalleryFileItem1, PublicGalleryFiles1

async def public_gallery_get_public_files_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  gallery: PublicGalleryModule = request.app.state.public_gallery
  rows = await gallery.list_public_files()
  files = [PublicGalleryFileItem1(**row) for row in rows]
  payload = PublicGalleryFiles1(files=files)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

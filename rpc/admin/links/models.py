from pydantic import BaseModel
from rpc.models import LinkItem

class AdminLinksHome1(BaseModel):
  links: list[LinkItem]

import json, os
from pathlib import Path
from fastapi import FastAPI
from . import BaseModule

class PermCapModule(BaseModule):
  def __init__(self, app: FastAPI, metadata_file: str | None = None):
    super().__init__(app)
    root = Path(__file__).resolve().parents[1]
    self.metadata_file = metadata_file or os.path.join(root, 'rpc', 'metadata.json')
    self.capabilities: dict[str, int] = {}

  async def startup(self):
    await self.load()

  async def shutdown(self):
    return

  async def load(self):
    try:
      with open(self.metadata_file, 'r') as f:
        data = json.load(f)
      self.capabilities = {i['op']: i.get('capabilities', 0) for i in data.get('rpc', [])}
    except FileNotFoundError:
      self.capabilities = {}

  def get_capabilities(self, op: str) -> int:
    return self.capabilities.get(op, 0)

  def filter_routes(self, routes: list[dict], role_mask: int) -> list[dict]:
    allowed: list[dict] = []
    for r in routes:
      req_mask = r.get('required_roles') or r.get('element_roles') or 0
      if req_mask == 0 or req_mask & role_mask == req_mask:
        allowed.append(r)
    return allowed


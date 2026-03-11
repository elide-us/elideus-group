from typing import Optional

from pydantic import BaseModel

# Static list of supported API providers — hardcoded for now
API_PROVIDERS = ["openai", "lumalabs"]


class SystemModelsModelItem1(BaseModel):
  recid: int
  name: str
  api_provider: str = "openai"
  is_active: bool = True


class SystemModelsList1(BaseModel):
  models: list[SystemModelsModelItem1]
  api_providers: list[str] = API_PROVIDERS


class SystemModelsUpsertModel1(BaseModel):
  recid: Optional[int] = None
  name: str
  api_provider: str = "openai"
  is_active: bool = True


class SystemModelsDeleteModel1(BaseModel):
  recid: Optional[int] = None
  name: Optional[str] = None

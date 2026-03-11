from typing import Optional

from pydantic import BaseModel


class DiscordPersonasModelItem1(BaseModel):
  recid: int
  name: str


class DiscordPersonasModels1(BaseModel):
  models: list[DiscordPersonasModelItem1]


class DiscordPersonasPersonaItem1(BaseModel):
  recid: Optional[int] = None
  name: str
  prompt: str
  tokens: int
  models_recid: int
  model: Optional[str] = None
  is_active: bool = True


class DiscordPersonasList1(BaseModel):
  personas: list[DiscordPersonasPersonaItem1]


class DiscordPersonasUpsertPersona1(BaseModel):
  recid: Optional[int] = None
  name: str
  prompt: str
  tokens: int
  models_recid: int
  is_active: bool = True


class DiscordPersonasDeletePersona1(BaseModel):
  recid: Optional[int] = None
  name: Optional[str] = None

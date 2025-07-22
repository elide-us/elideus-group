from pydantic import BaseModel

class ConfigItem(BaseModel):
  key: str
  value: str

class AdminConfigList1(BaseModel):
  items: list[ConfigItem]

class AdminConfigUpdate1(ConfigItem):
  pass

class AdminConfigDelete1(BaseModel):
  key: str

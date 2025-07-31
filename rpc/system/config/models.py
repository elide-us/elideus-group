from pydantic import BaseModel


class ConfigItem(BaseModel):
  key: str
  value: str

class SystemConfigList1(BaseModel):
  items: list[ConfigItem]

class SystemConfigUpdate1(ConfigItem):
  pass

class SystemConfigDelete1(BaseModel):
  key: str


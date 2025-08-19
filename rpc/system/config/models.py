from pydantic import BaseModel


class SystemConfigConfigItem1(BaseModel):
  key: str
  value: str


class SystemConfigList1(BaseModel):
  items: list[SystemConfigConfigItem1]


class SystemConfigDeleteConfig1(BaseModel):
  key: str

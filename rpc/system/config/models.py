from typing import Optional

from pydantic import BaseModel


class SystemConfigItem1(BaseModel):
  key: str
  value: Optional[str]

class SystemConfigList1(BaseModel):
  items: list[SystemConfigItem1]

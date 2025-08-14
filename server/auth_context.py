from typing import Any, Optional

from pydantic import BaseModel, Field

class AuthContext(BaseModel):
  user_guid: Optional[str] = None
  role_mask: int = 0
  roles: list[str] = Field(default_factory=list)
  provider: Optional[str] = None
  claims: dict[str, Any] = Field(default_factory=dict)

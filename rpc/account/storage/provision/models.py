from pydantic import BaseModel


class StorageProvisionStatus1(BaseModel):
  exists: bool

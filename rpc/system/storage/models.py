from pydantic import BaseModel


class SystemStorageStats1(BaseModel):
  file_count: int
  total_bytes: int
  folder_count: int
  user_folder_count: int
  db_rows: int


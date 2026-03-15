from pydantic import BaseModel


class FinanceDimensionsItem1(BaseModel):
  recid: int | None = None
  name: str
  value: str
  description: str | None = None
  status: int = 1


class FinanceDimensionsList1(BaseModel):
  dimensions: list[FinanceDimensionsItem1]


class FinanceDimensionsListByName1(BaseModel):
  name: str


class FinanceDimensionsGet1(BaseModel):
  recid: int


class FinanceDimensionsUpsert1(FinanceDimensionsItem1):
  pass


class FinanceDimensionsDelete1(BaseModel):
  recid: int

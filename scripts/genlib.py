from typing import Any, get_type_hints
from pydantic import BaseModel

PY_TO_TS = {
  str: 'string',
  int: 'number',
  float: 'number',
  bool: 'boolean',
  list: "array",
  dict: "object",
  type(None): "null",
}

def field_to_ts(name: str, annotation: Any) -> str:
  """Convert a single Pydantic field to TypeScript."""
  ts_type = PY_TO_TS.get(annotation, 'any')
  return f"  {name}: {ts_type};"

def model_to_ts(cls: type[BaseModel]) -> str:
  fields = []
  hints = get_type_hints(cls, include_extras=True)
  for name, typ in hints.items():
    fields.append(field_to_ts(name, typ))
  body = "\n".join(fields)
  return f"export interface {cls.__name__} {{\n{body}\n}}\n"
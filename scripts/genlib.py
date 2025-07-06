# from typing import Any, get_type_hints
# from pydantic import BaseModel

# PY_TO_TS = {
#   str: 'string',
#   int: 'number',
#   float: 'number',
#   bool: 'boolean',
#   list: "array",
#   dict: "object",
#   type(None): "null",
# }

# def field_to_ts(name: str, annotation: Any) -> str:
#   """Convert a single Pydantic field to TypeScript."""
#   ts_type = PY_TO_TS.get(annotation, 'any')
#   return f"  {name}: {ts_type};"

# def model_to_ts(cls: type[BaseModel]) -> str:
#   fields = []
#   hints = get_type_hints(cls, include_extras=True)
#   for name, typ in hints.items():
#     fields.append(field_to_ts(name, typ))
#   body = "\n".join(fields)
#   return f"export interface {cls.__name__} {{\n{body}\n}}\n"

# genlib.py

from typing import Any, Union, get_origin, get_args
from pydantic import BaseModel

# Map bare Python types to TS primitives (won't be used for generic types)
PY_TO_TS = {
    str: 'string',
    int: 'number',
    float: 'number',
    bool: 'boolean',
    type(None): 'null',
    dict: 'Record<string, any>',
    list: 'any[]',  # fallback for untyped list
}

def py_to_ts(py_type: Any) -> str:
    origin = get_origin(py_type)
    args = get_args(py_type)

    # Handle generics: List[X] or Tuple[X, ...]
    if origin in (list, tuple):
        inner_type = py_to_ts(args[0]) if args else 'any'
        return f"{inner_type}[]"

    # Handle Optional[X] (i.e. Union[X, None])
    if origin is Union:
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1:
            return f"{py_to_ts(non_none[0])} | null"
        return " | ".join(py_to_ts(arg) for arg in args)

    # Known primitives
    if py_type in PY_TO_TS:
        return PY_TO_TS[py_type]

    # Pydantic models → use interface name
    if isinstance(py_type, type) and issubclass(py_type, BaseModel):
        return py_type.__name__

    # Fallback
    return 'any'

def model_to_ts(model: type[BaseModel]) -> str:
    """
    Generate a TS interface from a Pydantic model.
    Works with Pydantic v2 (model.model_fields) or v1 (__fields__).
    """
    lines = [f"export interface {model.__name__} {{"]
    # Try Pydantic v2
    fields = getattr(model, 'model_fields', None) or getattr(model, '__fields__', {})
    for name, field in fields.items():
        # field.annotation is v2; outer_type_ exists in both v1/v2
        annotation = getattr(field, 'annotation', None) or getattr(field, 'outer_type_', None)
        ts_type = py_to_ts(annotation)
        lines.append(f"  {name}: {ts_type};")
    lines.append("}")
    return "\n".join(lines)

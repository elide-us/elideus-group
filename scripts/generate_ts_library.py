#!/usr/bin/env python3
"""Generate TypeScript interfaces from Pydantic models under the rpc folder."""

from __future__ import annotations

import inspect
import os
import importlib.util
from pydantic import BaseModel
from typing import get_type_hints, Any

ROOT = os.path.join(os.path.dirname(__file__), '..', 'rpc')

PY_TO_TS = {
    str: 'string',
    int: 'number',
    float: 'number',
    bool: 'boolean',
}


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("mod", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def field_to_ts(name: str, annotation: Any) -> str:
    ts_type = PY_TO_TS.get(annotation, 'any')
    return f"  {name}: {ts_type};"


def model_to_ts(cls: type[BaseModel]) -> str:
    fields = []
    hints = get_type_hints(cls, include_extras=True)
    for name, typ in hints.items():
        fields.append(field_to_ts(name, typ))
    body = "\n".join(fields)
    return f"export interface {cls.__name__} {{\n{body}\n}}\n"


def main() -> None:
    interfaces: list[str] = []
    for root, _, files in os.walk(ROOT):
        if 'models.py' in files:
            path = os.path.join(root, 'models.py')
            module = load_module(path)
            for _, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
                    interfaces.append(model_to_ts(obj))

    out_path = os.path.join(ROOT, '..', 'generated_rpc_models.ts')
    with open(out_path, 'w') as f:
        f.write("\n".join(interfaces))


if __name__ == "__main__":
    main()


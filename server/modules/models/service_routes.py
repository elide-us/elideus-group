from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class ServiceRouteItem:
  path: str
  name: str
  icon: str | None = None
  sequence: int = 0
  required_roles: list[str] = field(default_factory=list)

  @classmethod
  def from_dict(cls, data: dict | None) -> ServiceRouteItem:
    if not data:
      raise ValueError('Route item data is required')
    return cls(
      path=data.get('path', ''),
      name=data.get('name', ''),
      icon=data.get('icon'),
      sequence=int(data.get('sequence', 0)),
      required_roles=list(data.get('required_roles') or []),
    )

  def to_dict(self) -> dict:
    return {
      'path': self.path,
      'name': self.name,
      'icon': self.icon,
      'sequence': self.sequence,
      'required_roles': list(self.required_roles),
    }


@dataclass(slots=True)
class ServiceRouteCollection:
  routes: list[ServiceRouteItem] = field(default_factory=list)

  @classmethod
  def from_items(cls, items: Iterable[ServiceRouteItem]) -> ServiceRouteCollection:
    return cls(routes=list(items))

  def to_dict(self) -> dict:
    return {'routes': [route.to_dict() for route in self.routes]}


@dataclass(slots=True)
class ServiceRouteDelete:
  path: str

  @classmethod
  def from_dict(cls, data: dict | None) -> ServiceRouteDelete:
    if not data or 'path' not in data:
      raise ValueError('Route delete payload requires a path')
    return cls(path=data['path'])

  def to_dict(self) -> dict:
    return {'path': self.path}

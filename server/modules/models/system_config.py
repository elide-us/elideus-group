from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SystemConfigItem:
  key: str
  value: str


@dataclass(slots=True)
class SystemConfigList:
  items: list[SystemConfigItem]


@dataclass(slots=True)
class SystemConfigDeleteResult:
  key: str

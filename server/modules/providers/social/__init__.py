"""Base classes for social input providers."""

from __future__ import annotations

import asyncio
from abc import ABC
from typing import Any, Callable, TYPE_CHECKING

from .. import LifecycleProvider

__all__ = ["SocialInputProvider"]

if TYPE_CHECKING:  # pragma: no cover
  from ...social_input_module import SocialInputModule


class SocialInputProvider(LifecycleProvider, ABC):
  name: str

  def __init__(self, module: "SocialInputModule"):
    super().__init__()
    self.module = module

  async def dispatch(self, action: str, *args, **kwargs) -> Any:
    handler_name = f"handle_{action}"
    handler: Callable[..., Any] | None = getattr(self, handler_name, None)
    if not handler:
      raise ValueError(f"Action '{action}' not supported by provider '{self.name}'")
    result = handler(*args, **kwargs)
    if asyncio.iscoroutine(result):
      return await result
    return result

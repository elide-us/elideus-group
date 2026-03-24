"""Coordinator module for billing import providers."""

from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING

from fastapi import FastAPI

from . import BaseModule

if TYPE_CHECKING:  # pragma: no cover
  from .providers.billing import BillingImportProvider


class BillingImportModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: Dict[str, "BillingImportProvider"] = {}

  async def startup(self):
    from .providers.billing.azure_cost_details_provider import AzureCostDetailsProvider
    from .providers.billing.azure_invoice_provider import AzureInvoiceProvider

    provider = AzureCostDetailsProvider(self)
    await self.register_provider(provider)

    invoice_provider = AzureInvoiceProvider(self)
    await self.register_provider(invoice_provider)

    logging.info("[BillingImportModule] loaded providers: %s", list(self.providers.keys()))
    self.app.state.billing_import = self
    self.app.state.azure_billing_import = self
    self.mark_ready()

  async def shutdown(self):
    for name, provider in list(self.providers.items()):
      try:
        await provider.shutdown()
      except Exception:
        logging.exception("[BillingImportModule] Failed to shut down provider %s", name)
      finally:
        state_key = f"billing_{name}"
        if getattr(self.app.state, state_key, None) is provider:
          delattr(self.app.state, state_key)
        del self.providers[name]

    if getattr(self.app.state, 'billing_import', None) is self:
      self.app.state.billing_import = None
    if getattr(self.app.state, 'azure_billing_import', None) is self:
      self.app.state.azure_billing_import = None

  async def register_provider(self, provider: "BillingImportProvider"):
    name = provider.name
    if name in self.providers:
      raise ValueError(f"Billing provider '{name}' already registered")
    await provider.startup()
    self.providers[name] = provider
    setattr(self.app.state, f"billing_{name}", provider)

  def get_provider(self, name: str) -> "BillingImportProvider | None":
    return self.providers.get(name)

  async def run_import(self, provider_name: str, **kwargs: Any) -> dict:
    provider = self.providers.get(provider_name)
    if not provider:
      raise ValueError(f"Billing provider '{provider_name}' not registered")
    return await provider.run_import(**kwargs)

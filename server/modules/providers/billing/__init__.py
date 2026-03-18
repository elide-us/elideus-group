"""Base classes for billing import providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from .. import LifecycleProvider

if TYPE_CHECKING:  # pragma: no cover
  from ...billing_import_module import BillingImportModule


class BillingImportProvider(LifecycleProvider, ABC):
  """Base class for all billing data import providers.

  Each provider knows how to fetch billing data from a single external source
  (Azure Cost Details, Azure Invoices, OpenAI Usage, etc.) and normalize it
  into the shared staging tables (finance_staging_imports, finance_staging_line_items).
  """

  name: str

  def __init__(self, module: "BillingImportModule"):
    super().__init__()
    self.module = module

  @abstractmethod
  async def run_import(self, **kwargs: Any) -> dict:
    """Execute an import. Returns a dict with import_recid, status, row_count, etc."""
    ...

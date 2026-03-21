from __future__ import annotations

import asyncio
from types import SimpleNamespace

from server.jobs.billing_import_pipeline import BillingImportPipelineHandler


def test_create_journal_uses_pipeline_config_values():
  requested_configs: list[tuple[str, str]] = []
  created_payload: dict | None = None

  class _Finance:
    async def on_ready(self):
      return None

    async def list_periods(self):
      return [
        {
          "guid": "period-guid",
          "start_date": "2025-01-01",
          "end_date": "2025-01-31",
        }
      ]

    async def get_pipeline_config(self, pipeline: str, key: str) -> str:
      requested_configs.append((pipeline, key))
      lookup = {
        ("billing_import", "ap_account_number"): "2200",
        ("billing_import", "default_dimension_recids"): "[15,4]",
        ("billing_import", "source_type_invoice"): "azure_invoice",
        ("billing_import", "source_type_usage"): "azure_billing_import",
      }
      return lookup[(pipeline, key)]

    async def _get_account_guid_by_number(self, number: str) -> str:
      assert number == "2200"
      return "ap-guid"

    async def create_journal(self, **kwargs):
      nonlocal created_payload
      created_payload = kwargs
      return {"recid": 91}

  app = SimpleNamespace(state=SimpleNamespace(finance=_Finance()))
  context = {
    "imports_recid": 42,
    "import_metadata": {"element_period_start": "2025-01-15"},
    "classified_costs": [
      {
        "accounts_guid": "expense-guid",
        "amount": "12.50000",
        "service": "Microsoft.Sql",
        "meter_category": "Databases",
        "record_type": "invoice",
      }
    ],
    "ledgers_recid": 8,
  }

  result = asyncio.run(BillingImportPipelineHandler.create_journal(app, {}, context))

  assert result == {
    "journal_recid": 91,
    "posting_summary": {
      "posting_key": "AZURE-IMPORT-42",
      "periods_guid": "period-guid",
      "line_count": 2,
      "total": "12.50000",
    },
  }
  assert requested_configs == [
    ("billing_import", "ap_account_number"),
    ("billing_import", "default_dimension_recids"),
    ("billing_import", "source_type_invoice"),
    ("billing_import", "source_type_usage"),
  ]
  assert created_payload is not None
  assert created_payload["source_type"] == "azure_invoice"
  assert created_payload["lines"][0]["dimension_recids"] == [15, 4]
  assert created_payload["lines"][1]["accounts_guid"] == "ap-guid"



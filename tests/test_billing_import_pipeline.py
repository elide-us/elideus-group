import asyncio
from types import SimpleNamespace

from queryregistry.models import DBResponse
from server.jobs.billing_import_pipeline import BillingImportPipelineHandler


class FakeDb:
  def __init__(self):
    self.import_status_updates = []

  async def on_ready(self):
    return None

  async def run(self, request):
    if request.op == "db:finance:staging:list_imports:1":
      return DBResponse(
        rows=[
          {
            "recid": 77,
            "element_status": 1,
            "element_row_count": 3,
            "element_period_start": "2025-01-05",
            "element_period_end": "2025-01-31",
          }
        ]
      )
    if request.op == "db:finance:staging_line_items:aggregate_line_items:1":
      return DBResponse(
        rows=[
          {
            "element_service": "Microsoft.Compute",
            "element_category": "Virtual Machines",
            "element_total_amount": "10.50",
            "element_row_count": 2,
            "element_record_type": "usage",
          },
          {
            "element_service": "Microsoft.Cache",
            "element_category": "Redis",
            "element_total_amount": "2.00",
            "element_row_count": 1,
            "element_record_type": "usage",
          },
        ]
      )

    if request.op == "db:finance:staging_line_items:list_line_items_by_import:1":
      return DBResponse(rows=[{"vendors_recid": 1}])
    if request.op == "db:finance:staging_account_map:resolve_account:1":
      service_name = request.payload.get("service_name")
      if service_name == "Microsoft.Compute":
        return DBResponse(
          rows=[
            {
              "accounts_guid": "exp-guid",
              "element_service_pattern": "Microsoft.Compute",
              "account_number": "6100",
              "account_name": "Cloud Compute",
            }
          ]
        )
      return DBResponse(
        rows=[
          {
            "accounts_guid": "wild-guid",
            "element_service_pattern": "*",
            "account_number": "6199",
            "account_name": "Cloud Misc",
          }
        ]
      )
    if request.op == "db:finance:staging:update_import_status:1":
      self.import_status_updates.append(dict(request.payload))
      return DBResponse(rows=[])
    raise AssertionError(f"unexpected query op: {request.op}")


class FakeFinance:
  def __init__(self):
    self.created_journals = {}
    self.last_create_payload = None

  async def on_ready(self):
    return None

  async def list_accounts(self):
    return [
      {"guid": "exp-guid", "number": "6100", "name": "Cloud Compute"},
      {"guid": "wild-guid", "number": "6199", "name": "Cloud Misc"},
      {"guid": "ap-guid", "number": "2200", "name": "Accounts Payable"},
    ]

  async def _get_account_guid_by_number(self, number):
    if number == "2200":
      return "ap-guid"
    raise ValueError("unknown account")

  async def list_periods(self):
    return [
      {
        "guid": "period-jan",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
      }
    ]

  async def create_journal(self, **kwargs):
    self.last_create_payload = kwargs
    posting_key = kwargs["posting_key"]
    if posting_key in self.created_journals:
      return self.created_journals[posting_key]
    created = {"recid": len(self.created_journals) + 500, "status": 1, "posting_key": posting_key}
    self.created_journals[posting_key] = created
    return created

  async def post_journal(self, recid):
    return {"recid": recid, "status": 1}


def test_pipeline_steps_through_all_stages_and_tracks_wildcard_warning():
  db = FakeDb()
  finance = FakeFinance()
  app = SimpleNamespace(state=SimpleNamespace(db=db, finance=finance))
  handler = BillingImportPipelineHandler()

  async def run_pipeline():
    payload = {"imports_recid": 77}
    context = {}
    for _, step in handler.steps:
      step_result = await step(app, payload, context)
      context.update(step_result or {})
    return context

  result = asyncio.run(run_pipeline())

  assert result["imports_recid"] == 77
  assert result["journal_recid"] == 500
  assert result["import_status"] == 3
  assert result["classified_costs"][0]["record_type"] == "usage"
  assert result["warnings"] == [
    {
      "service": "Microsoft.Cache",
      "meter_category": "Redis",
      "accounts_guid": "wild-guid",
      "warning": "service matched wildcard catch-all",
    }
  ]
  assert db.import_status_updates == [{"recid": 77, "status": 3, "row_count": 3, "error": None}]


def test_create_journal_selects_period_by_import_start_date():
  finance = FakeFinance()
  app = SimpleNamespace(state=SimpleNamespace(finance=finance))

  context = {
    "imports_recid": 77,
    "import_metadata": {"element_period_start": "2025-01-05"},
    "classified_costs": [{"accounts_guid": "exp-guid", "service": "Microsoft.Compute", "meter_category": "Virtual Machines", "amount": "10.50", "record_type": "usage"}],
  }
  result = asyncio.run(BillingImportPipelineHandler.create_journal(app, {"imports_recid": 77}, context))

  assert result["posting_summary"]["periods_guid"] == "period-jan"
  assert finance.last_create_payload["periods_guid"] == "period-jan"
  assert finance.last_create_payload["source_type"] == "azure_billing_import"


def test_create_journal_is_idempotent_for_same_posting_key():
  finance = FakeFinance()
  app = SimpleNamespace(state=SimpleNamespace(finance=finance))
  context = {
    "imports_recid": 77,
    "import_metadata": {"element_period_start": "2025-01-05"},
    "classified_costs": [{"accounts_guid": "exp-guid", "service": "Microsoft.Compute", "meter_category": "Virtual Machines", "amount": "10.50", "record_type": "usage"}],
  }

  first = asyncio.run(BillingImportPipelineHandler.create_journal(app, {"imports_recid": 77}, dict(context)))
  second = asyncio.run(BillingImportPipelineHandler.create_journal(app, {"imports_recid": 77}, dict(context)))

  assert first["journal_recid"] == second["journal_recid"]
  assert first["posting_summary"]["posting_key"] == "AZURE-IMPORT-77"


def test_create_journal_uses_invoice_source_type_for_invoice_only_batches():
  finance = FakeFinance()
  app = SimpleNamespace(state=SimpleNamespace(finance=finance))

  context = {
    "imports_recid": 77,
    "import_metadata": {"element_period_start": "2025-01-05"},
    "classified_costs": [{"accounts_guid": "exp-guid", "service": "AzureServices", "meter_category": "Invoice", "amount": "10.50", "record_type": "invoice"}],
  }
  asyncio.run(BillingImportPipelineHandler.create_journal(app, {"imports_recid": 77}, context))

  assert finance.last_create_payload["source_type"] == "azure_invoice"
  assert finance.last_create_payload["lines"][0]["description"].startswith("Azure Invoice")

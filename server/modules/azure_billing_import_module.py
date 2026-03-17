"""Azure billing import module for Cost Details staging ingestion."""

from __future__ import annotations

import asyncio
import csv
from datetime import datetime
import io
import json
import logging
import re

import aiohttp
from azure.identity.aio import ClientSecretCredential
from fastapi import FastAPI

from queryregistry.finance.staging import (
  create_import_request,
  insert_cost_detail_batch_request,
  update_import_status_request,
)
from queryregistry.finance.staging_invoices import (
  get_invoice_by_name_request,
  insert_invoice_batch_request,
)
from queryregistry.finance.staging_purge_log import check_purged_key_request
from queryregistry.finance.staging_line_items import insert_line_items_batch_request
from queryregistry.finance.staging.models import (
  CreateImportParams,
  InsertCostDetailBatchParams,
  UpdateImportStatusParams,
)
from queryregistry.finance.staging_invoices.models import (
  GetInvoiceByNameParams,
  InsertInvoiceBatchParams,
)
from queryregistry.finance.staging_purge_log.models import CheckPurgedKeyParams
from queryregistry.finance.staging_line_items.models import InsertLineItemsBatchParams
from queryregistry.finance.vendors import get_vendor_by_name_request
from queryregistry.finance.vendors.models import GetVendorByNameParams
from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams

from . import BaseModule
from .db_module import DbModule
from .env_module import EnvModule


class AzureBillingImportModule(BaseModule):
  _START_DATE_AFTER_PATTERN = re.compile(
    r"Start\s+date\s+must\s+be\s+after\s+"
    r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)",
    re.IGNORECASE,
  )

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self._tenant_id: str | None = None
    self._client_id: str | None = None
    self._client_secret: str | None = None
    self._subscription_id: str | None = None
    self._credential: ClientSecretCredential | None = None
    self._credential_tenant_id: str | None = None
    self._credential_client_id: str | None = None
    self._credential_client_secret: str | None = None
    self._azure_vendor_recid: int | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.env = self.app.state.env
    await self.env.on_ready()

    self._client_id = await self._load_config("AzureBillingClientId")
    self._tenant_id = await self._load_config("AzureBillingTenantId")
    self._subscription_id = await self._load_config("AzureBillingSubscriptionId")
    try:
      self._client_secret = self.env.get("AZURE_BILLING_CLIENT_SECRET") if self.env else None
    except Exception:
      self._client_secret = None

    if not self._client_id:
      logging.warning("[AzureBillingImportModule] Missing config value for key: AzureBillingClientId")
    if not self._tenant_id:
      logging.warning("[AzureBillingImportModule] Missing config value for key: AzureBillingTenantId")
    if not self._subscription_id:
      logging.warning(
        "[AzureBillingImportModule] Missing config value for key: AzureBillingSubscriptionId",
      )
    if not self._client_secret:
      logging.warning(
        "[AzureBillingImportModule] Missing env value for key: AZURE_BILLING_CLIENT_SECRET",
      )

    self.app.state.azure_billing_import = self
    self.mark_ready()

  async def shutdown(self):
    if self._credential:
      await self._credential.close()
      self._credential = None
    self._credential_tenant_id = None
    self._credential_client_id = None
    self._credential_client_secret = None
    self._tenant_id = None
    self._client_id = None
    self._client_secret = None
    self._subscription_id = None
    self._azure_vendor_recid = None
    self.db = None
    self.env = None

  async def _load_config(self, key: str) -> str:
    if not self.db:
      raise RuntimeError("AzureBillingImportModule requires database module")
    res = await self.db.run(get_config_request(ConfigKeyParams(key=key)))
    if not res.rows:
      return ""
    return res.rows[0].get("element_value") or ""

  async def _get_management_token(self) -> str:
    """Acquire an Azure Management API access token via client credentials."""
    if not self.env:
      raise RuntimeError("AzureBillingImportModule requires environment module")
    try:
      self._client_secret = self.env.get("AZURE_BILLING_CLIENT_SECRET")
    except Exception:
      self._client_secret = None

    if not all([self._tenant_id, self._client_id, self._client_secret]):
      raise ValueError("Azure AD credentials not configured")

    if (
      not self._credential
      or self._credential_tenant_id != self._tenant_id
      or self._credential_client_id != self._client_id
      or self._credential_client_secret != self._client_secret
    ):
      if self._credential:
        await self._credential.close()
      self._credential = ClientSecretCredential(
        tenant_id=self._tenant_id,
        client_id=self._client_id,
        client_secret=self._client_secret,
      )
      self._credential_tenant_id = self._tenant_id
      self._credential_client_id = self._client_id
      self._credential_client_secret = self._client_secret

    token = await self._credential.get_token("https://management.azure.com/.default")
    return token.token

  def _parse_retry_after(self, value: str | None, default: int = 60) -> int:
    if not value:
      return default
    try:
      parsed = int(value)
    except ValueError:
      return default
    return max(1, min(parsed, 300))

  def _parse_start_date_after_error(self, response_text: str) -> datetime | None:
    match = self._START_DATE_AFTER_PATTERN.search(response_text)
    if not match:
      return None
    return datetime.strptime(match.group(1), "%m/%d/%Y %I:%M:%S %p")


  @staticmethod
  def _to_decimal(value: str | None) -> str | None:
    if value is None:
      return None
    cleaned = str(value).strip()
    if not cleaned:
      return None
    try:
      return str(float(cleaned))
    except ValueError:
      return None

  @staticmethod
  def _to_iso_date(value: str | None) -> str | None:
    if value is None:
      return None
    raw = str(value).strip()
    if not raw:
      return None
    return raw[:10]


  @staticmethod
  def _to_azure_date(iso_date: str) -> str:
    """Convert YYYY-MM-DD to MM-DD-YYYY for Azure Billing API."""
    parts = iso_date.split("-")
    return f"{parts[1]}-{parts[2]}-{parts[0]}"

  async def import_cost_details(
    self,
    period_start: str,
    period_end: str,
    metric: str = "ActualCost",
  ) -> dict:
    if not self.db:
      raise RuntimeError("AzureBillingImportModule requires database module")

    import_recid: int | None = None
    total_rows = 0
    status = "failed"

    try:
      if not self._subscription_id:
        raise ValueError("Azure billing subscription not configured")

      token = await self._get_management_token()

      create_res = await self.db.run(
        create_import_request(
          CreateImportParams(
            source="azure_cost_details",
            scope=f"subscriptions/{self._subscription_id}",
            metric=metric,
            period_start=period_start,
            period_end=period_end,
          ),
        ),
      )
      if not create_res.rows:
        raise RuntimeError("Failed to create finance staging import record")
      import_recid = int(create_res.rows[0]["recid"])

      url = (
        "https://management.azure.com/subscriptions/"
        f"{self._subscription_id}/providers/Microsoft.CostManagement/"
        "generateCostDetailsReport?api-version=2025-03-01"
      )
      headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
      }
      body = {
        "metric": metric,
        "timePeriod": {
          "start": period_start,
          "end": period_end,
        },
      }

      async with aiohttp.ClientSession() as session:
        corrected_start: str | None = None
        for attempt in range(2):
          async with session.post(url, headers=headers, json=body) as response:
            if response.status == 202:
              location = response.headers.get("Location")
              retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
              if not location:
                raise RuntimeError("Azure Cost Details report response missing Location header")
              break

            response_text = await response.text()
            if response.status != 400 or attempt == 1:
              raise RuntimeError(
                "Azure Cost Details report request failed "
                f"({response.status}): {response_text}",
              )

            corrected_start_dt = self._parse_start_date_after_error(response_text)
            if not corrected_start_dt:
              raise RuntimeError(
                "Azure Cost Details report request failed "
                f"({response.status}): {response_text}",
              )

            corrected_start = corrected_start_dt.isoformat(timespec="seconds")
            logging.info(
              "[AzureBillingImportModule] Auto-corrected Azure Cost Details start date from %s to %s",
              body["timePeriod"]["start"],
              corrected_start,
            )
            body["timePeriod"]["start"] = corrected_start
        else:
          raise RuntimeError("Azure Cost Details report request failed with unknown retry state")

        manifest: dict | None = None
        while True:
          await asyncio.sleep(retry_after)
          async with session.get(location, headers=headers) as poll_response:
            poll_payload = await poll_response.json(content_type=None)
            if poll_response.status >= 400:
              raise RuntimeError(
                "Azure Cost Details poll failed "
                f"({poll_response.status}): {poll_payload}",
              )
            poll_status = (poll_payload.get("status") or "").strip()
            retry_after = self._parse_retry_after(poll_response.headers.get("Retry-After"))
            if poll_status == "Completed":
              manifest = poll_payload.get("manifest") or {}
              break
            if poll_status == "Failed":
              error_payload = poll_payload.get("error") or poll_payload
              raise RuntimeError(f"Azure Cost Details report failed: {error_payload}")

        blobs = manifest.get("blobs") if isinstance(manifest, dict) else None
        if not isinstance(blobs, list) or not blobs:
          raise RuntimeError("Azure Cost Details manifest missing blobs")
        blob_link = blobs[0].get("blobLink") if isinstance(blobs[0], dict) else None
        if not blob_link:
          raise RuntimeError("Azure Cost Details blob link missing from manifest")

        async with session.get(blob_link) as blob_response:
          if blob_response.status >= 400:
            response_text = await blob_response.text()
            raise RuntimeError(
              "Azure Cost Details blob download failed "
              f"({blob_response.status}): {response_text}",
            )
          csv_text = await blob_response.text()
          csv_text = csv_text.lstrip("\ufeff")

      vendor_lookup = await self.db.run(
        get_vendor_by_name_request(GetVendorByNameParams(element_name="Azure")),
      )
      if not vendor_lookup.rows:
        raise ValueError("Missing finance vendor seed row for Azure")
      vendors_recid = int(vendor_lookup.rows[0]["recid"])

      csv_reader = csv.DictReader(io.StringIO(csv_text))
      raw_batch: list[dict[str, object]] = []
      normalized_batch: list[dict[str, object]] = []
      for row in csv_reader:
        clean_row = {key: value for key, value in row.items() if key}
        raw_batch.append(clean_row)
        normalized_batch.append(
          {
            "element_date": self._to_iso_date(clean_row.get("element_Date") or clean_row.get("Date")),
            "element_service": clean_row.get("ConsumedService"),
            "element_category": clean_row.get("MeterCategory"),
            "element_description": clean_row.get("MeterName"),
            "element_quantity": self._to_decimal(clean_row.get("Quantity")),
            "element_unit_price": self._to_decimal(clean_row.get("EffectivePrice")),
            "element_amount": self._to_decimal(clean_row.get("CostInBillingCurrency")) or "0",
            "element_currency": clean_row.get("BillingCurrency"),
            "element_raw_json": json.dumps(clean_row),
          },
        )
        if len(raw_batch) >= 100:
          await self.db.run(
            insert_cost_detail_batch_request(
              InsertCostDetailBatchParams(imports_recid=import_recid, rows=raw_batch),
            ),
          )
          await self.db.run(
            insert_line_items_batch_request(
              InsertLineItemsBatchParams(
                imports_recid=import_recid,
                vendors_recid=vendors_recid,
                rows=normalized_batch,
              ),
            ),
          )
          total_rows += len(raw_batch)
          raw_batch = []
          normalized_batch = []

      if raw_batch:
        await self.db.run(
          insert_cost_detail_batch_request(
            InsertCostDetailBatchParams(imports_recid=import_recid, rows=raw_batch),
          ),
        )
        await self.db.run(
          insert_line_items_batch_request(
            InsertLineItemsBatchParams(
              imports_recid=import_recid,
              vendors_recid=vendors_recid,
              rows=normalized_batch,
            ),
          ),
        )
        total_rows += len(raw_batch)

      await self.db.run(
        update_import_status_request(
          UpdateImportStatusParams(
            recid=import_recid,
            status=1,
            row_count=total_rows,
            error=None,
          ),
        ),
      )
      status = "completed"
      return {
        "import_recid": import_recid,
        "status": status,
        "row_count": total_rows,
      }
    except Exception as exc:
      logging.exception("[AzureBillingImportModule] Cost details import failed")
      if import_recid and self.db:
        try:
          await self.db.run(
            update_import_status_request(
              UpdateImportStatusParams(
                recid=import_recid,
                status=2,
                row_count=total_rows,
                error=str(exc),
              ),
            ),
          )
        except Exception:
          logging.exception("[AzureBillingImportModule] Failed to update import failure status")
      raise

  async def import_invoices(self, period_start: str, period_end: str) -> dict:
    if not self.db:
      raise RuntimeError("AzureBillingImportModule requires database module")

    import_recid: int | None = None
    inserted_count = 0
    skipped_count = 0

    try:
      if not self._subscription_id:
        raise ValueError("Azure billing subscription not configured")

      token = await self._get_management_token()

      if self._azure_vendor_recid is None:
        vendor_lookup = await self.db.run(
          get_vendor_by_name_request(GetVendorByNameParams(element_name="Azure")),
        )
        if not vendor_lookup.rows:
          raise ValueError("Missing finance vendor seed row for Azure")
        self._azure_vendor_recid = int(vendor_lookup.rows[0]["recid"])

      create_res = await self.db.run(
        create_import_request(
          CreateImportParams(
            source="azure_invoices",
            scope=f"subscriptions/{self._subscription_id}",
            metric="Invoices",
            period_start=period_start,
            period_end=period_end,
          ),
        ),
      )
      if not create_res.rows:
        raise RuntimeError("Failed to create finance staging import record")
      import_recid = int(create_res.rows[0]["recid"])

      url = (
        "https://management.azure.com/providers/Microsoft.Billing/"
        "billingAccounts/default/billingSubscriptions/"
        f"{self._subscription_id}/invoices"
      )
      params = {
        "periodStartDate": self._to_azure_date(period_start[:10]),
        "periodEndDate": self._to_azure_date(period_end[:10]),
        "api-version": "2024-04-01",
      }
      headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
      }

      raw_batch: list[dict[str, object]] = []
      normalized_batch: list[dict[str, object]] = []

      async with aiohttp.ClientSession() as session:
        next_url: str | None = url
        next_params: dict[str, str] | None = params

        while next_url:
          async with session.get(next_url, headers=headers, params=next_params) as response:
            payload = await response.json(content_type=None)
            if response.status >= 400:
              raise RuntimeError(
                "Azure invoice request failed "
                f"({response.status}): {payload}",
              )

          for invoice in payload.get("value") or []:
            name = invoice.get("name")
            if not name:
              continue

            existing = await self.db.run(
              get_invoice_by_name_request(GetInvoiceByNameParams(invoice_name=str(name))),
            )
            if existing.rows:
              skipped_count += 1
              continue

            purged = await self.db.run(
              check_purged_key_request(
                CheckPurgedKeyParams(vendors_recid=self._azure_vendor_recid, key=str(name))
              )
            )
            purged_row = None
            if purged.rows:
              purged_row = purged.rows[0] if isinstance(purged.rows, list) else purged.rows
            if purged_row and int(purged_row.get("found") or 0) == 1:
              skipped_count += 1
              continue

            props = invoice.get("properties") or {}
            billed_amount = (props.get("billedAmount") or {}).get("value")
            billed_currency = (props.get("billedAmount") or {}).get("currency")
            raw_batch.append(
              {
                "element_invoice_name": name,
                "element_invoice_date": self._to_iso_date(props.get("invoiceDate")),
                "element_invoice_period_start": self._to_iso_date(props.get("invoicePeriodStartDate")),
                "element_invoice_period_end": self._to_iso_date(props.get("invoicePeriodEndDate")),
                "element_due_date": self._to_iso_date(props.get("dueDate")),
                "element_invoice_type": props.get("invoiceType"),
                "element_status": props.get("status"),
                "element_billed_amount": billed_amount,
                "element_amount_due": (props.get("amountDue") or {}).get("value"),
                "element_currency": billed_currency,
                "element_subscription_id": props.get("subscriptionId"),
                "element_subscription_name": props.get("subscriptionDisplayName"),
                "element_purchase_order": props.get("purchaseOrderNumber"),
                "element_raw_json": json.dumps(invoice),
              }
            )
            normalized_batch.append(
              {
                "element_date": self._to_iso_date(props.get("invoiceDate")),
                "element_service": props.get("invoiceType"),
                "element_category": "Invoice",
                "element_description": f"Azure Invoice {name} — {props.get('subscriptionDisplayName') or ''}".rstrip(),
                "element_quantity": 1,
                "element_unit_price": billed_amount,
                "element_amount": billed_amount,
                "element_currency": billed_currency,
                "element_raw_json": json.dumps(invoice),
                "element_record_type": "invoice",
              }
            )

          if len(raw_batch) >= 100:
            await self.db.run(
              insert_invoice_batch_request(
                InsertInvoiceBatchParams(imports_recid=import_recid, rows=raw_batch),
              ),
            )
            await self.db.run(
              insert_line_items_batch_request(
                InsertLineItemsBatchParams(
                  imports_recid=import_recid,
                  vendors_recid=self._azure_vendor_recid,
                  rows=normalized_batch,
                ),
              ),
            )
            inserted_count += len(raw_batch)
            raw_batch = []
            normalized_batch = []

          next_url = payload.get("nextLink")
          next_params = None

      if raw_batch:
        await self.db.run(
          insert_invoice_batch_request(
            InsertInvoiceBatchParams(imports_recid=import_recid, rows=raw_batch),
          ),
        )
        await self.db.run(
          insert_line_items_batch_request(
            InsertLineItemsBatchParams(
              imports_recid=import_recid,
              vendors_recid=self._azure_vendor_recid,
              rows=normalized_batch,
            ),
          ),
        )
        inserted_count += len(raw_batch)

      await self.db.run(
        update_import_status_request(
          UpdateImportStatusParams(
            recid=import_recid,
            status=1,
            row_count=inserted_count,
            error=None,
          ),
        ),
      )
      return {
        "import_recid": import_recid,
        "status": "completed",
        "invoice_count": inserted_count,
        "skipped_count": skipped_count,
      }
    except Exception as exc:
      logging.exception("[AzureBillingImportModule] Invoice import failed")
      if import_recid and self.db:
        try:
          await self.db.run(
            update_import_status_request(
              UpdateImportStatusParams(
                recid=import_recid,
                status=2,
                row_count=inserted_count,
                error=str(exc),
              ),
            ),
          )
        except Exception:
          logging.exception("[AzureBillingImportModule] Failed to update invoice import failure status")
      raise

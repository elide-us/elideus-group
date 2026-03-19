"""Azure invoice billing import provider."""

from __future__ import annotations

from calendar import monthrange
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
import logging
from typing import Any, TYPE_CHECKING

import aiohttp
from azure.identity.aio import ClientSecretCredential

from queryregistry.finance.staging import create_import_request, update_import_status_request
from queryregistry.finance.staging.models import CreateImportParams, UpdateImportStatusParams
from queryregistry.finance.staging_invoices import get_invoice_by_name_request, insert_invoice_batch_request
from queryregistry.finance.staging_invoices.models import GetInvoiceByNameParams, InsertInvoiceBatchParams
from queryregistry.finance.staging_line_items import insert_line_items_batch_request
from queryregistry.finance.staging_line_items.models import InsertLineItemsBatchParams
from queryregistry.finance.staging_purge_log import check_purged_key_request
from queryregistry.finance.staging_purge_log.models import CheckPurgedKeyParams
from queryregistry.finance.vendors import get_vendor_by_name_request
from queryregistry.finance.vendors.models import GetVendorByNameParams
from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams

from ...db_module import DbModule
from ...env_module import EnvModule
from . import BillingImportProvider

if TYPE_CHECKING:  # pragma: no cover
  from ...billing_import_module import BillingImportModule


class AzureInvoiceProvider(BillingImportProvider):
  name = "azure_invoices"

  def __init__(self, module: "BillingImportModule"):
    super().__init__(module)
    self.db: DbModule | None = None
    self.env: EnvModule | None = None
    self._tenant_id: str | None = None
    self._client_id: str | None = None
    self._client_secret: str | None = None
    self._subscription_id: str | None = None
    self._billing_account_id: str | None = None
    self._credential: ClientSecretCredential | None = None
    self._credential_tenant_id: str | None = None
    self._credential_client_id: str | None = None
    self._credential_client_secret: str | None = None
    self._azure_vendor_recid: int | None = None

  async def startup(self):
    self.db = self.module.app.state.db
    await self.db.on_ready()
    self.env = self.module.app.state.env
    await self.env.on_ready()

    self._client_id = await self._load_config("AzureBillingClientId")
    self._tenant_id = await self._load_config("AzureBillingTenantId")
    self._subscription_id = await self._load_config("AzureBillingSubscriptionId")
    self._billing_account_id = await self._load_config("AzureBillingAccountId")
    try:
      self._client_secret = self.env.get("AZURE_BILLING_CLIENT_SECRET") if self.env else None
    except Exception:
      self._client_secret = None

    if not self._client_id:
      logging.warning("[AzureInvoiceProvider] Missing config value for key: AzureBillingClientId")
    if not self._tenant_id:
      logging.warning("[AzureInvoiceProvider] Missing config value for key: AzureBillingTenantId")
    if not self._subscription_id:
      logging.warning("[AzureInvoiceProvider] Missing config value for key: AzureBillingSubscriptionId")
    if not self._billing_account_id:
      logging.warning("[AzureInvoiceProvider] Missing config value for key: AzureBillingAccountId")
    if not self._client_secret:
      logging.warning("[AzureInvoiceProvider] Missing env value for key: AZURE_BILLING_CLIENT_SECRET")

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
    self._billing_account_id = None
    self._azure_vendor_recid = None
    self.db = None
    self.env = None

  async def run_import(self, **kwargs: Any) -> dict:
    return await self.import_invoices(period_month=kwargs["period_month"])

  async def _load_config(self, key: str) -> str:
    if not self.db:
      raise RuntimeError("AzureInvoiceProvider requires database module")
    res = await self.db.run(get_config_request(ConfigKeyParams(key=key)))
    if not res.rows:
      return ""
    return res.rows[0].get("element_value") or ""

  async def _get_management_token(self) -> str:
    if not self.env:
      raise RuntimeError("AzureInvoiceProvider requires environment module")
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

  async def _get_vendor_recid(self) -> int:
    if self._azure_vendor_recid is not None:
      return self._azure_vendor_recid
    if not self.db:
      raise RuntimeError("AzureInvoiceProvider requires database module")

    vendor_lookup = await self.db.run(
      get_vendor_by_name_request(GetVendorByNameParams(element_name="Azure")),
    )
    if not vendor_lookup.rows:
      raise ValueError("Missing finance vendor seed row for Azure")

    self._azure_vendor_recid = int(vendor_lookup.rows[0]["recid"])
    return self._azure_vendor_recid

  @staticmethod
  def _to_decimal(value) -> str | None:
    if value is None:
      return None
    cleaned = str(value).strip()
    if not cleaned:
      return None
    try:
      return format(Decimal(cleaned), "f")
    except (InvalidOperation, ValueError):
      return None

  @staticmethod
  def _to_iso_date(value) -> str | None:
    if value is None:
      return None
    raw = str(value).strip()
    if not raw:
      return None
    if len(raw) >= 10 and raw[4] == "-":
      return raw[:10]
    try:
      parsed = datetime.strptime(raw[:10], "%m/%d/%Y")
      return parsed.strftime("%Y-%m-%d")
    except ValueError:
      return raw[:10]

  @staticmethod
  def _extract_invoice_name(invoice_id: str) -> str:
    return invoice_id.rstrip("/").split("/")[-1]

  @staticmethod
  def _extract_money_amount(value: Any) -> str | None:
    if isinstance(value, dict):
      for key in ("amount", "value", "amountDue", "billedAmount"):
        if key in value:
          return AzureInvoiceProvider._to_decimal(value.get(key))
      return None
    return AzureInvoiceProvider._to_decimal(value)

  @staticmethod
  def _extract_money_currency(value: Any) -> str | None:
    if isinstance(value, dict):
      currency = value.get("currency") or value.get("currencyCode") or value.get("unit")
      if currency is None:
        return None
      cleaned = str(currency).strip()
      return cleaned or None
    return None

  @staticmethod
  def _build_line_item(invoice_name: str, properties: dict[str, Any], invoice_payload: dict[str, Any]) -> dict[str, Any]:
    billed_amount_value = properties.get("billedAmount")
    amount_due_value = properties.get("amountDue")
    billed_amount = AzureInvoiceProvider._extract_money_amount(billed_amount_value)
    amount_due = AzureInvoiceProvider._extract_money_amount(amount_due_value)
    currency = (
      AzureInvoiceProvider._extract_money_currency(billed_amount_value)
      or AzureInvoiceProvider._extract_money_currency(amount_due_value)
      or properties.get("currency")
      or properties.get("billingCurrency")
    )
    service = (
      properties.get("subscriptionName")
      or properties.get("subscriptionDisplayName")
      or properties.get("subscriptionId")
      or "Azure Invoice"
    )
    category = properties.get("invoiceType") or properties.get("type") or "Invoice"
    description = properties.get("purchaseOrder") or properties.get("purchaseOrderNumber")
    if description:
      description = f"Azure invoice {invoice_name} ({description})"
    else:
      description = f"Azure invoice {invoice_name}"

    return {
      "element_date": AzureInvoiceProvider._to_iso_date(
        properties.get("invoiceDate") or properties.get("dueDate") or properties.get("invoicePeriodEndDate"),
      ),
      "element_service": service,
      "element_category": category,
      "element_description": description,
      "element_quantity": "1.0",
      "element_unit_price": billed_amount or amount_due or "0",
      "element_amount": billed_amount or amount_due or "0",
      "element_currency": currency,
      "element_raw_json": json.dumps(invoice_payload),
      "element_record_type": "invoice",
    }

  @staticmethod
  def _build_invoice_row(
    invoice_name: str,
    subscription_id: str,
    properties: dict[str, Any],
    invoice_payload: dict[str, Any],
  ) -> dict[str, Any]:
    billed_amount_value = properties.get("billedAmount")
    amount_due_value = properties.get("amountDue")
    return {
      "element_invoice_name": invoice_name,
      "element_invoice_date": AzureInvoiceProvider._to_iso_date(properties.get("invoiceDate")),
      "element_invoice_period_start": AzureInvoiceProvider._to_iso_date(
        properties.get("invoicePeriodStartDate") or properties.get("billingPeriodStartDate"),
      ),
      "element_invoice_period_end": AzureInvoiceProvider._to_iso_date(
        properties.get("invoicePeriodEndDate") or properties.get("billingPeriodEndDate"),
      ),
      "element_due_date": AzureInvoiceProvider._to_iso_date(properties.get("dueDate")),
      "element_invoice_type": properties.get("invoiceType") or properties.get("type"),
      "element_status": properties.get("status"),
      "element_billed_amount": AzureInvoiceProvider._extract_money_amount(billed_amount_value),
      "element_amount_due": AzureInvoiceProvider._extract_money_amount(amount_due_value),
      "element_currency": (
        AzureInvoiceProvider._extract_money_currency(billed_amount_value)
        or AzureInvoiceProvider._extract_money_currency(amount_due_value)
        or properties.get("currency")
        or properties.get("billingCurrency")
      ),
      "element_subscription_id": properties.get("subscriptionId") or subscription_id,
      "element_subscription_name": (
        properties.get("subscriptionName")
        or properties.get("subscriptionDisplayName")
        or properties.get("displayName")
      ),
      "element_purchase_order": properties.get("purchaseOrder") or properties.get("purchaseOrderNumber"),
      "element_raw_json": json.dumps(invoice_payload),
    }

  async def import_invoices(self, period_month: str) -> dict[str, Any]:
    if not self.db:
      raise RuntimeError("AzureInvoiceProvider requires database module")
    if not self._subscription_id:
      raise ValueError("Azure billing subscription not configured")
    if not self._billing_account_id:
      raise ValueError("Azure billing account ID not configured (set AzureBillingAccountId in system_config)")

    import_recid: int | None = None
    invoice_count = 0
    skipped_count = 0

    try:
      parsed_month = datetime.strptime(period_month, "%Y-%m")
      if parsed_month.strftime("%Y-%m") != period_month:
        raise ValueError
    except ValueError as exc:
      raise ValueError("period_month must be in YYYY-MM format") from exc

    period_start = f"{period_month}-01"
    period_end = f"{period_month}-{monthrange(parsed_month.year, parsed_month.month)[1]:02d}"

    try:
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

      vendor_recid = await self._get_vendor_recid()
      token = await self._get_management_token()
      headers = {"Authorization": f"Bearer {token}"}

      invoices_list_url = (
        "https://management.azure.com/providers/Microsoft.Billing/"
        f"billingAccounts/{self._billing_account_id}/invoices"
      )
      invoices_list_params = {
        "api-version": "2024-04-01",
        "periodStartDate": period_start,
        "periodEndDate": period_end,
      }

      invoice_rows: list[dict[str, Any]] = []
      line_item_rows: list[dict[str, Any]] = []
      invoice_names_seen: set[str] = set()
      discovered_invoice_names: list[str] = []

      async with aiohttp.ClientSession() as session:
        logging.info(
          "[AzureInvoiceProvider] Fetching invoices list url=%s params=%s",
          invoices_list_url,
          invoices_list_params,
        )
        async with session.get(invoices_list_url, headers=headers, params=invoices_list_params) as response:
          response_text = await response.text()
          if response.status >= 400:
            logging.error(
              "[AzureInvoiceProvider] Invoices list request failed status=%s body=%s",
              response.status,
              response_text[:500],
            )
            raise RuntimeError(
              f"Azure invoices list request failed ({response.status}): {response_text[:500]}",
            )
          payload = json.loads(response_text or "{}")

        invoices = payload.get("value") or []
        logging.info(
          "[AzureInvoiceProvider] Invoices list response count=%s url=%s",
          len(invoices),
          invoices_list_url,
        )

        for invoice in invoices:
          invoice_name = invoice.get("name")
          if not invoice_name:
            logging.warning("[AzureInvoiceProvider] Skipping invoice with missing name payload=%s", invoice)
            continue
          if invoice_name in invoice_names_seen:
            continue
          invoice_names_seen.add(invoice_name)
          discovered_invoice_names.append(invoice_name)

          existing = await self.db.run(
            get_invoice_by_name_request(GetInvoiceByNameParams(invoice_name=invoice_name)),
          )
          if existing.rows:
            skipped_count += 1
            logging.info("[AzureInvoiceProvider] Skipping existing invoice_name=%s", invoice_name)
            continue

          purged = await self.db.run(
            check_purged_key_request(CheckPurgedKeyParams(vendors_recid=vendor_recid, key=invoice_name)),
          )
          if purged.rows:
            skipped_count += 1
            logging.info("[AzureInvoiceProvider] Skipping purged invoice_name=%s", invoice_name)
            continue

          properties = invoice.get("properties") or {}
          invoice_rows.append(
            self._build_invoice_row(
              invoice_name=invoice_name,
              subscription_id=self._subscription_id,
              properties=properties,
              invoice_payload=invoice,
            ),
          )
          line_item_rows.append(self._build_line_item(invoice_name, properties, invoice))

        if not discovered_invoice_names:
          message = (
            f"No Azure invoices found for billing account "
            f"{self._billing_account_id} in period {period_month}."
          )
          logging.info(
            "[AzureInvoiceProvider] Summary invoices_found=0 inserted=0 skipped=0",
          )
          await self.db.run(
            update_import_status_request(
              UpdateImportStatusParams(recid=import_recid, status=1, row_count=0, error=None),
            ),
          )
          return {
            "import_recid": import_recid,
            "status": "completed",
            "invoice_count": 0,
            "skipped_count": 0,
            "message": message,
          }

        if invoice_rows:
          await self.db.run(
            insert_invoice_batch_request(
              InsertInvoiceBatchParams(imports_recid=import_recid, rows=invoice_rows),
            ),
          )
          await self.db.run(
            insert_line_items_batch_request(
              InsertLineItemsBatchParams(
                imports_recid=import_recid,
                vendors_recid=vendor_recid,
                rows=line_item_rows,
              ),
            ),
          )
          invoice_count = len(invoice_rows)

        message = (
          f"Imported {invoice_count} Azure invoice(s) for {period_month}; skipped {skipped_count}."
        )
        logging.info(
          "[AzureInvoiceProvider] Summary invoices_found=%s inserted=%s skipped=%s",
          len(discovered_invoice_names),
          invoice_count,
          skipped_count,
        )
        await self.db.run(
          update_import_status_request(
            UpdateImportStatusParams(
              recid=import_recid,
              status=1,
              row_count=invoice_count,
              error=None,
            ),
          ),
        )
        return {
          "import_recid": import_recid,
          "status": "completed",
          "invoice_count": invoice_count,
          "skipped_count": skipped_count,
          "message": message,
        }
    except Exception as exc:
      logging.exception("[AzureInvoiceProvider] Invoice import failed")
      if import_recid and self.db:
        try:
          await self.db.run(
            update_import_status_request(
              UpdateImportStatusParams(
                recid=import_recid,
                status=2,
                row_count=invoice_count,
                error=str(exc),
              ),
            ),
          )
        except Exception:
          logging.exception("[AzureInvoiceProvider] Failed to update import failure status")
      raise

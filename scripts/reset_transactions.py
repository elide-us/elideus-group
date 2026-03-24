from __future__ import annotations

import argparse
import asyncio
import sys

import aioodbc
from dotenv import load_dotenv


DELETE_STATEMENTS = [
  # DELETE is used instead of TRUNCATE because several parent tables in this
  # cascade are referenced by foreign keys, and TRUNCATE would fail even when
  # child rows are removed first.

  # Staging cascade
  ('finance_staging_line_items', 'DELETE FROM finance_staging_line_items;'),
  ('finance_staging_azure_invoices', 'DELETE FROM finance_staging_azure_invoices;'),
  ('finance_staging_azure_cost_details', 'DELETE FROM finance_staging_azure_cost_details;'),
  ('finance_staging_imports', 'DELETE FROM finance_staging_imports;'),
  ('finance_staging_purge_log', 'DELETE FROM finance_staging_purge_log;'),
  ('finance_staging_account_map', 'DELETE FROM finance_staging_account_map;'),
  ('finance_vendors', 'DELETE FROM finance_vendors;'),

  # Journal cascade
  ('finance_journal_line_dimensions', 'DELETE FROM finance_journal_line_dimensions;'),
  ('finance_journal_lines', 'DELETE FROM finance_journal_lines;'),
  ('finance_journals', 'DELETE FROM finance_journals;'),

  # Credit lots cascade
  ('finance_credit_lot_events', 'DELETE FROM finance_credit_lot_events;'),
  ('finance_credit_lots', 'DELETE FROM finance_credit_lots;'),

  # Async tasks cascade
  ('system_async_task_events', 'DELETE FROM system_async_task_events;'),
  ('system_async_tasks', 'DELETE FROM system_async_tasks;'),

  # Batch job history (preserve job definitions)
  ('system_batch_job_history', 'DELETE FROM system_batch_job_history;'),
]

SEQUENCE_RESETS = [
  (
    'JRN-SEQ',
    "UPDATE finance_numbers SET element_last_number = 0, element_modified_on = SYSUTCDATETIME() WHERE element_account_number = 'JRN-SEQ';",
  ),
  (
    'LOT-SEQ',
    "UPDATE finance_numbers SET element_last_number = 0, element_modified_on = SYSUTCDATETIME() WHERE element_account_number = 'LOT-SEQ';",
  ),
]

RESEED_TABLES = [
  'finance_staging_line_items',
  'finance_staging_azure_invoices',
  'finance_staging_azure_cost_details',
  'finance_staging_imports',
  'finance_staging_purge_log',
  'finance_staging_account_map',
  'finance_vendors',
  'finance_journal_line_dimensions',
  'finance_journal_lines',
  'finance_journals',
  'finance_credit_lot_events',
  'finance_credit_lots',
  'system_async_task_events',
  'system_async_tasks',
  'system_batch_job_history',
]

SEED_STATUS_CODES = """
DELETE FROM finance_status_codes;

INSERT INTO finance_status_codes (element_domain, element_code, element_name, element_description)
VALUES
  ('import', 0, 'pending', 'Import created, awaiting processing'),
  ('import', 1, 'approved', 'Import approved for promotion'),
  ('import', 2, 'failed', 'Import processing failed'),
  ('import', 3, 'promoted', 'Import promoted to journal'),
  ('import', 4, 'pending_approval', 'Import completed, awaiting manager approval'),
  ('import', 5, 'rejected', 'Import rejected'),
  ('journal', 0, 'draft', 'Journal created, not yet submitted'),
  ('journal', 1, 'pending_approval', 'Journal submitted, awaiting manager approval'),
  ('journal', 2, 'posted', 'Journal approved and posted to general ledger'),
  ('journal', 3, 'reversed', 'Journal has been reversed'),
  ('period', 1, 'open', 'Period is open for posting'),
  ('period', 2, 'closed', 'Period is closed, no new postings'),
  ('period', 3, 'locked', 'Period is locked, no modifications'),
  ('period_close_type', 0, 'none', 'Not a closing period'),
  ('period_close_type', 1, 'quarterly', 'Quarterly closing period'),
  ('period_close_type', 2, 'annual', 'Annual closing period'),
  ('async_task', 0, 'queued', 'Task queued for processing'),
  ('async_task', 1, 'running', 'Task is currently running'),
  ('async_task', 2, 'polling', 'Task is polling for external result'),
  ('async_task', 3, 'waiting_callback', 'Task waiting for callback'),
  ('async_task', 4, 'completed', 'Task completed successfully'),
  ('async_task', 5, 'failed', 'Task failed'),
  ('async_task', 6, 'cancelled', 'Task was cancelled'),
  ('async_task', 7, 'timed_out', 'Task timed out'),
  ('element', 0, 'inactive', 'Record is inactive/deleted'),
  ('element', 1, 'active', 'Record is active'),
  ('credit_lot', 1, 'active', 'Credit lot is active and available'),
  ('credit_lot', 2, 'exhausted', 'Credit lot fully consumed'),
  ('credit_lot', 3, 'expired', 'Credit lot has expired');
"""

SEED_PIPELINE_CONFIG = """
DELETE FROM finance_pipeline_config;

INSERT INTO finance_pipeline_config (element_pipeline, element_key, element_value, element_description)
VALUES
  ('billing_import', 'ap_account_number', '2200', 'Accounts payable contra account for billing imports'),
  ('billing_import', 'default_dimension_recids', '[15,4]', 'Default dimension recids applied to billing import journal lines'),
  ('billing_import', 'source_type_invoice', 'azure_invoice', 'Source type string for Azure invoice imports'),
  ('billing_import', 'source_type_usage', 'azure_billing_import', 'Source type string for Azure usage/cost imports'),
  ('credit_consumption', 'deferred_revenue_account_number', '2100', 'Deferred revenue account debited on credit consumption'),
  ('credit_consumption', 'revenue_account_number', '4010', 'Revenue account credited on credit consumption'),
  ('credit_purchase', 'cash_account_number', '1100', 'Cash account debited on credit purchase'),
  ('credit_purchase', 'deferred_revenue_account_number', '2100', 'Deferred revenue account credited on credit purchase');
"""

SEED_VENDORS = """
DELETE FROM finance_vendors;

INSERT INTO finance_vendors (element_name, element_display, element_description, element_status)
VALUES
  ('Azure', 'Microsoft Azure', 'Microsoft Azure billing source', 1),
  ('OpenAI', 'OpenAI API', 'OpenAI API billing source', 1),
  ('Luma', 'Luma Labs API', 'Luma Labs API billing source', 1),
  ('Claude', 'Anthropic (Claude)', 'Monthly subscription for Claude Max (Apple)', 1),
  ('NameCom', 'Name.com', 'Name.com domain registrar', 1),
  ('Microsoft', 'Microsoft 365', 'Microsoft 365 subscription billing source', 1),
  ('ChatGPT', 'OpenAI (ChatGPT)', 'Monthly subscription for OpenAI ChatGPT (Apple)', 1),
  ('Anthropic', 'Anthropic API', 'Anthropic API usage source', 1);
"""

SEED_ACCOUNT_MAP = """
DELETE FROM finance_staging_account_map;

INSERT INTO finance_staging_account_map (
  vendors_recid, element_service_pattern, element_meter_pattern,
  accounts_guid, element_priority, element_description, element_status
)
VALUES
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), 'Microsoft.Web', NULL, 'FB72A666-E9C3-47B5-A3D8-7A93D2132FC5', 10, 'Azure App Service → 5120 Cloud Hosting', 1),
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), '*', NULL, 'FB72A666-E9C3-47B5-A3D8-7A93D2132FC5', 0, 'Catch-all for unmapped Azure services', 1),
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), 'Microsoft.Storage', NULL, '8CA13447-27EB-4087-8465-8B79716B2352', 10, 'Azure Storage', 1),
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), 'Microsoft.Sql', NULL, 'C9BF5326-60A7-45A0-AF1F-A0E0BED6CD71', 10, 'Azure SQL Database', 1),
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), 'Microsoft.Network', NULL, '79330229-D980-4C92-A5BD-CA96ED9818A5', 10, 'Azure Networking', 1),
  ((SELECT recid FROM finance_vendors WHERE element_name = 'Azure'), 'Microsoft.ContainerRegistry', NULL, 'D3E406AF-03D0-4CBE-BC05-CE737E20F6F3', 10, 'Azure Container Registry', 1),
  (NULL, 'Azure Invoice', NULL, 'FB72A666-E9C3-47B5-A3D8-7A93D2132FC5', 10, 'Azure Invoice summary line', 1);
"""

SEED_STATEMENTS = [
  ('finance_status_codes', 29, SEED_STATUS_CODES),
  ('finance_pipeline_config', 8, SEED_PIPELINE_CONFIG),
  ('finance_vendors', 8, SEED_VENDORS),
  ('finance_staging_account_map', 7, SEED_ACCOUNT_MAP),
]

TARGET_ENV_VARS = {
  'test': 'AZURE_SQL_CONNECTION_STRING_DEV',
  'prod': 'AZURE_SQL_CONNECTION_STRING',
}


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Reset transactional finance/system data.')
  parser.add_argument('--apply', action='store_true', help='Execute deletion and reset operations')
  parser.add_argument(
    '--target',
    choices=('test', 'prod'),
    default='test',
    help='Database target: test uses AZURE_SQL_CONNECTION_STRING_DEV, prod uses AZURE_SQL_CONNECTION_STRING',
  )
  return parser.parse_args()


def prefixed_line(text: str, apply: bool) -> str:
  if apply:
    return text
  return f'[dry-run] {text}'


def confirm_target(target: str) -> None:
  if target != 'prod':
    return

  print('⚠️  WARNING: You are targeting the PRODUCTION database.')
  confirmation = input("Type 'CONFIRM PROD' to proceed: ")
  if confirmation != 'CONFIRM PROD':
    print('Production reset cancelled.', file=sys.stderr)
    raise SystemExit(1)


async def connect_pool(target: str) -> aioodbc.Pool:
  import os

  load_dotenv()
  env_var = TARGET_ENV_VARS[target]
  dsn = os.environ.get(env_var)
  if not dsn:
    print(f'{env_var} is not set.', file=sys.stderr)
    raise SystemExit(1)

  try:
    return await asyncio.wait_for(aioodbc.create_pool(dsn=dsn, autocommit=True), timeout=10)
  except (asyncio.TimeoutError, Exception) as exc:
    print(f'Unable to connect to database: {exc}', file=sys.stderr)
    raise SystemExit(1)


async def run_delete_phase(cursor: aioodbc.Cursor, apply: bool) -> None:
  print(prefixed_line('=== Phase 1: Delete transactional data ===', apply))
  for table_name, delete_sql in DELETE_STATEMENTS:
    if apply:
      await cursor.execute(delete_sql)
      print(prefixed_line(f'  DELETED  {table_name}  ({cursor.rowcount} rows)', apply))
      continue

    await cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
    count_row = await cursor.fetchone()
    row_count = count_row[0] if count_row else 0
    print(prefixed_line(f'  DELETED  {table_name}  ({row_count} rows)', apply))


async def run_sequence_phase(cursor: aioodbc.Cursor, apply: bool) -> None:
  print()
  print(prefixed_line('=== Phase 2: Reset number sequences ===', apply))
  for sequence_name, sequence_sql in SEQUENCE_RESETS:
    if apply:
      await cursor.execute(sequence_sql)
    print(prefixed_line(f'  RESET    {sequence_name}', apply))


async def run_reseed_phase(cursor: aioodbc.Cursor, apply: bool) -> None:
  print()
  print(prefixed_line('=== Phase 3: Reseed identity columns ===', apply))
  for table_name in RESEED_TABLES:
    if apply:
      await cursor.execute(f"DBCC CHECKIDENT ('{table_name}', RESEED, 0);")
    print(prefixed_line(f'  RESEED   {table_name}', apply))


async def run_seed_phase(cursor: aioodbc.Cursor, apply: bool) -> None:
  print()
  print(prefixed_line('=== Phase 4: Re-seed finance configuration ===', apply))
  for table_name, row_count, seed_sql in SEED_STATEMENTS:
    if apply:
      await cursor.execute(seed_sql)
    print(prefixed_line(f'  SEED     {table_name} ({row_count} rows)', apply))


async def run(apply: bool, target: str) -> None:
  confirm_target(target)
  pool = await connect_pool(target)
  try:
    async with pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await run_delete_phase(cursor, apply)
        await run_sequence_phase(cursor, apply)
        await run_reseed_phase(cursor, apply)
        await run_seed_phase(cursor, apply)
  finally:
    pool.close()
    await pool.wait_closed()

  print()
  if apply:
    print('✓ Reset complete.')
    return
  print('[dry-run] No changes made. Use --apply to execute.')


def main() -> None:
  args = parse_args()
  asyncio.run(run(args.apply, args.target))


if __name__ == '__main__':
  main()

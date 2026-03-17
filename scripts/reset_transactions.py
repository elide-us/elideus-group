from __future__ import annotations

import argparse
import asyncio
import sys

import aioodbc
from dotenv import load_dotenv


DELETE_STATEMENTS = [
  # Staging cascade
  ('finance_staging_line_items', 'DELETE FROM finance_staging_line_items;'),
  ('finance_staging_azure_invoices', 'DELETE FROM finance_staging_azure_invoices;'),
  ('finance_staging_azure_cost_details', 'DELETE FROM finance_staging_azure_cost_details;'),
  ('finance_staging_imports', 'DELETE FROM finance_staging_imports;'),
  ('finance_staging_purge_log', 'DELETE FROM finance_staging_purge_log;'),

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
  'finance_journal_line_dimensions',
  'finance_journal_lines',
  'finance_journals',
  'finance_credit_lot_events',
  'finance_credit_lots',
  'system_async_task_events',
  'system_async_tasks',
  'system_batch_job_history',
]


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Reset transactional finance/system data.')
  parser.add_argument('--apply', action='store_true', help='Execute deletion and reset operations')
  return parser.parse_args()


def prefixed_line(text: str, apply: bool) -> str:
  if apply:
    return text
  return f'[dry-run] {text}'


async def connect_pool() -> aioodbc.Pool:
  import os

  load_dotenv()
  dsn = os.environ.get('AZURE_SQL_CONNECTION_STRING_DEV')
  if not dsn:
    print('AZURE_SQL_CONNECTION_STRING_DEV is not set.', file=sys.stderr)
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


async def run(apply: bool) -> None:
  pool = await connect_pool()
  try:
    async with pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await run_delete_phase(cursor, apply)
        await run_sequence_phase(cursor, apply)
        await run_reseed_phase(cursor, apply)
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
  asyncio.run(run(args.apply))


if __name__ == '__main__':
  main()

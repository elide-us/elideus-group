"""Unit tests for the dependency-free cron evaluator (server/helpers/cron.py).

Pure logic, no DB. The two expressions the automation schema actually carries
(`0 */12 * * *` storage_reindex, `*/5 * * * *` stall_monitor) are covered
explicitly, plus the cases a hand-written evaluator gets wrong: the Sunday=0/7
duality, cron's OR between day-of-month and day-of-week, and refusing
expressions it cannot represent instead of guessing.
"""

from datetime import datetime, timezone

import pytest

from server.helpers.cron import CronError, matches, next_run, parse_cron

UTC = timezone.utc


def at(y, mo, d, h, mi):
  return datetime(y, mo, d, h, mi, tzinfo=UTC)


# ── the two live expressions ────────────────────────────────────────────────

def test_stall_monitor_every_five_minutes():
  assert matches('*/5 * * * *', at(2026, 7, 24, 13, 0))
  assert matches('*/5 * * * *', at(2026, 7, 24, 13, 55))
  assert not matches('*/5 * * * *', at(2026, 7, 24, 13, 1))


def test_storage_reindex_every_twelve_hours():
  assert matches('0 */12 * * *', at(2026, 7, 24, 0, 0))
  assert matches('0 */12 * * *', at(2026, 7, 24, 12, 0))
  assert not matches('0 */12 * * *', at(2026, 7, 24, 6, 0))
  assert not matches('0 */12 * * *', at(2026, 7, 24, 12, 1))


# ── next_run ────────────────────────────────────────────────────────────────

def test_next_run_is_strictly_after():
  # Already matching: must advance, not return the same minute and re-fire.
  assert next_run('*/5 * * * *', at(2026, 7, 24, 13, 0)) == at(2026, 7, 24, 13, 5)


def test_next_run_rolls_over_the_day():
  assert next_run('0 */12 * * *', at(2026, 7, 24, 12, 30)) == at(2026, 7, 25, 0, 0)


def test_next_run_naive_datetime_treated_as_utc():
  assert next_run('*/5 * * * *', datetime(2026, 7, 24, 13, 0)) == at(2026, 7, 24, 13, 5)


def test_impossible_date_returns_none():
  assert next_run('0 0 30 2 *', at(2026, 1, 1, 0, 0)) is None   # 30 February


# ── field forms ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize('expr,moment,expected', [
  ('30 2 * * *',      at(2026, 7, 24, 2, 30),  True),
  ('0 9-17 * * *',    at(2026, 7, 24, 12, 0),  True),
  ('0 9-17 * * *',    at(2026, 7, 24, 18, 0),  False),
  ('0 0,12 * * *',    at(2026, 7, 24, 12, 0),  True),
  ('0 0-23/6 * * *',  at(2026, 7, 24, 18, 0),  True),
  ('0 0-23/6 * * *',  at(2026, 7, 24, 19, 0),  False),
])
def test_field_forms(expr, moment, expected):
  assert matches(expr, moment) is expected


def test_sunday_is_both_zero_and_seven():
  sunday = at(2026, 7, 26, 0, 0)
  assert sunday.weekday() == 6           # Python Sunday
  assert matches('0 0 * * 0', sunday)
  assert matches('0 0 * * 7', sunday)


def test_day_of_month_and_day_of_week_are_ORed_not_ANDed():
  # Cron's historical behaviour: when BOTH are restricted, either may match.
  # ANDing here would silently make jobs fire far less often than intended.
  first = at(2026, 7, 1, 0, 0)           # 1st, a Wednesday
  assert first.weekday() == 2
  assert matches('0 0 1 * 0', first)     # matches on day-of-month alone
  sunday = at(2026, 7, 26, 0, 0)
  assert matches('0 0 1 * 0', sunday)    # matches on day-of-week alone


def test_unrestricted_dom_and_dow_matches_every_day():
  assert matches('0 0 * * *', at(2026, 7, 24, 0, 0))


# ── refusals: better to fail than to silently mean something else ───────────

@pytest.mark.parametrize('expr', [
  '@daily',                  # alias
  '* * * *',                 # 4 fields
  '0 0 * * * *',             # 6 fields (seconds)
  '0 0 * * MON',             # name form
  '99 * * * *',              # out of range
  '0 0 * * 1#2',             # nth-weekday
  '*/0 * * * *',             # zero step
  '', '   ',
])
def test_unsupported_expressions_raise(expr):
  with pytest.raises(CronError):
    parse_cron(expr)


def test_next_run_validates_before_looping():
  # Must raise immediately, not spin through a year of candidate minutes.
  with pytest.raises(CronError):
    next_run('@hourly', at(2026, 7, 24, 0, 0))

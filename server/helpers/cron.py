"""Minimal 5-field cron evaluation for the automation scheduler.

Supports the standard five fields — minute hour day-of-month month day-of-week —
with `*`, `*/step`, `n`, `n-m`, `n-m/step`, and comma lists of those. That covers
every expression the automation schema carries (`0 */12 * * *`, `*/5 * * * *`)
and every realistic one a scheduled task would use.

Deliberately dependency-free rather than pulling in croniter for two
expressions. The trade-off is explicit: no `@yearly` aliases, no seconds field,
no `L`/`W`/`#` day-of-week specifiers. Any of those raise rather than being
silently misread — a schedule that quietly means something other than what it
says is worse than one that refuses to load.

Day-of-week is 0-6 with 0 = Sunday, and 7 is accepted as Sunday too (the common
Unix extension). When BOTH day-of-month and day-of-week are restricted, cron's
historical behaviour is OR, not AND — that is preserved here, because getting it
wrong silently changes when a job runs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

_FIELD_BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))
_FIELD_NAMES = ('minute', 'hour', 'day-of-month', 'month', 'day-of-week')
_MAX_LOOKAHEAD_MINUTES = 366 * 24 * 60  # a year; beyond this the expression never fires


class CronError(ValueError):
  """Raised for an expression this evaluator will not silently guess at."""


def _parse_field(spec: str, low: int, high: int, name: str) -> frozenset[int]:
  values: set[int] = set()
  for part in spec.split(','):
    part = part.strip()
    if not part:
      raise CronError(f'empty {name} element in {spec!r}')
    step = 1
    if '/' in part:
      part, _, step_text = part.partition('/')
      if not step_text.isdigit() or int(step_text) < 1:
        raise CronError(f'bad step {step_text!r} in {name}')
      step = int(step_text)
      part = part or '*'
    if part == '*':
      start, end = low, high
    elif '-' in part:
      a, _, b = part.partition('-')
      if not (a.isdigit() and b.isdigit()):
        raise CronError(f'bad range {part!r} in {name}')
      start, end = int(a), int(b)
    elif part.isdigit():
      start = end = int(part)
    else:
      raise CronError(f'unsupported {name} value {part!r}')

    if name == 'day-of-week':
      start = 0 if start == 7 else start
      end = 0 if end == 7 else end
      if end < start:
        start, end = end, start
    if start < low or end > high or end < start:
      raise CronError(f'{name} {part!r} out of range {low}-{high}')
    values.update(range(start, end + 1, step))

  if not values:
    raise CronError(f'{name} matched nothing in {spec!r}')
  return frozenset(values)


def parse_cron(expression: str) -> tuple[frozenset[int], ...]:
  fields = (expression or '').split()
  if len(fields) != 5:
    raise CronError(
      f'expected 5 cron fields, got {len(fields)} in {expression!r}. '
      'Aliases like @daily and 6-field (seconds) expressions are not supported.'
    )
  return tuple(
    _parse_field(spec, low, high, name)
    for spec, (low, high), name in zip(fields, _FIELD_BOUNDS, _FIELD_NAMES)
  )


def matches(expression: str, moment: datetime) -> bool:
  """True if `moment` (to the minute) satisfies the expression."""
  minute, hour, dom, month, dow = parse_cron(expression)
  if moment.minute not in minute or moment.hour not in hour or moment.month not in month:
    return False

  # Python weekday(): Monday=0..Sunday=6. Cron: Sunday=0..Saturday=6.
  cron_dow = (moment.weekday() + 1) % 7
  dom_restricted = len(dom) < 31
  dow_restricted = len(dow) < 7
  if dom_restricted and dow_restricted:
    return moment.day in dom or cron_dow in dow      # OR — cron's historical behaviour
  if dom_restricted:
    return moment.day in dom
  if dow_restricted:
    return cron_dow in dow
  return True


def next_run(expression: str, after: datetime) -> datetime | None:
  """First matching minute strictly after `after`, or None if it never fires
  within a year (a valid-but-impossible date like 30 February)."""
  parse_cron(expression)  # fail fast on a bad expression, before looping
  moment = (after.astimezone(timezone.utc) if after.tzinfo else after.replace(tzinfo=timezone.utc))
  moment = moment.replace(second=0, microsecond=0) + timedelta(minutes=1)
  for _ in range(_MAX_LOOKAHEAD_MINUTES):
    if matches(expression, moment):
      return moment
    moment += timedelta(minutes=1)
  return None

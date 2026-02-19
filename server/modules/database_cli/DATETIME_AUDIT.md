# Datetime / Temporal Audit (v0.8.0 Greenfield Alignment)

## Current Canonical Rules (v0.8.0+)

These rules are the active baseline for all new work:

1. **Only use `element_created_on` and `element_modified_on`** for row-level
   temporal audit columns.
2. **Use UTC-aware `datetimeoffset` semantics end-to-end** (SQL columns,
   Python datetimes, and serialized payloads).
3. **Do not add alias temporal fields** (`created_on` / `modified_on`) for
   compatibility shims in SQL, models, or response payloads.

## Enforcement Checklist for New SQL / Model Additions

Use this checklist whenever adding or changing SQL statements, typed records, or
Pydantic models that include temporal audit fields:

- [ ] SQL `SELECT`, `INSERT`, and `UPDATE` statements use
      `element_created_on` / `element_modified_on` (never bare
      `created_on` / `modified_on` for database row fields).
- [ ] SQL temporal columns and defaults are `datetimeoffset` with UTC behavior.
- [ ] Python datetime construction for DB writes is UTC-aware
      (`datetime.now(timezone.utc)` or equivalent normalized input).
- [ ] Datetime inputs are normalized to UTC before parameter binding.
- [ ] Pydantic/model fields use canonical names (`element_created_on`,
      `element_modified_on`) without aliases.
- [ ] ISO datetime parsing accepts `Z` and normalizes to UTC-aware values.

## Scope

Audited Python source under `server/` for:

1. Datetime construction used for database writes.
2. Bare `created_on` / `modified_on` references for user tables that now require
   `element_created_on` / `element_modified_on`.
3. `datetime2` casting/conversion usage in Python-authored SQL strings.
4. ODBC parameter typing hints requiring timestamp-type updates.
5. Pydantic temporal field handling for timezone-aware UTC values.
6. Query-registry SQL modules under `server/registry`.

## Appendix: historical changes

The following notes capture the remediation work completed during the v0.8.0
alignment effort.

### Findings and Fixes

### 1) Datetime construction for database writes

- **Issue found** in `server/registry/account/cache/mssql.py`:
  - `datetime.utcnow()` produced naive datetimes for `created_on` fallback.
  - `created_on`/`modified_on` inputs were passed through without timezone normalization.
- **Fix applied**:
  - Replaced naive fallback with `datetime.now(timezone.utc)`.
  - Added `_as_utc(...)` normalization helper used before SQL parameter binding.
  - Naive incoming datetimes are now coerced to UTC-aware (`tzinfo=timezone.utc`), and aware
    values are normalized to UTC.

### 2) Bare temporal column names for targeted user tables

- **Issue found** in `users_enablements` registry queries:
  - SQL selected bare `ue.created_on` and `ue.modified_on`.
  - Upsert update used bare `modified_on = SYSUTCDATETIME()`.
  - Typed record model exposed bare `created_on`/`modified_on` keys.
- **Fix applied**:
  - Updated SQL to use `element_created_on` and `element_modified_on`.
  - Updated update statement to set `element_modified_on`.
  - Updated typed record keys to `element_created_on` / `element_modified_on`.

### 3) `datetime2` cast/convert references

- No Python SQL statements in `server/` were found using explicit `datetime2` casts or converts.
- No change required.

### 4) ODBC/driver parameter type hints

- No `SQL_TYPE_TIMESTAMP` (or equivalent explicit timestamp parameter typing constants) were
  found in `server/` Python code.
- No change required.

### 5) Pydantic temporal field handling

- **Issue found** in `server/registry/account/cache/model.py`:
  - Temporal fields did not enforce exact schema-aligned element-prefixed names with strict datetime typing.
- **Fix applied**:
  - Renamed Python model fields to `element_created_on` and `element_modified_on`.
  - Added validator to parse ISO strings and normalize all values to UTC-aware datetimes.
  - Removed compatibility aliases/fallback mappings so payload keys now match database columns exactly.

- **Hardening applied** in `server/registry/account/session/model.py`:
  - Added UTC-normalizing validators for `CreateSessionParams` and `SetRotkeyParams` datetime fields.
  - Accepts ISO strings (including trailing `Z`) and normalizes all datetimes to UTC-aware values.

## Files Changed

- `server/registry/account/cache/mssql.py`
- `server/registry/account/cache/model.py`
- `server/registry/account/enablements/mssql.py`
- `server/registry/account/enablements/model.py`
- `server/registry/account/session/model.py`
- `server/modules/database_cli/DATETIME_AUDIT.md`

## Notes

- Per request, no SQL schema files were modified.
- **Zero backwards-compatibility aliases are maintained** for cache temporal fields; Python payload/model field names now match database column names exactly (`element_created_on`, `element_modified_on`).
- Storage-provider model property names such as `created_on` / `modified_on` remain unchanged where they represent provider SDK metadata rather than database row fields.

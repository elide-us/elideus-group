# **DEPRECATED: `server/registry/` is legacy and is being deleted domain-by-domain in favor of `queryregistry/`.**

Do **not** add new handlers, models, or operation names under this directory.
Do **not** maintain aliases, compatibility shims, or new fallbacks that keep this
layer alive. Each migrated domain is removed once its `queryregistry/` equivalent
is live.

For canonical query-registry patterns, read `queryregistry/AGENTS.md`.

---

## What this layer IS

- A **temporary legacy registry** that still serves unmigrated operations.
- A compatibility surface used only until equivalent operations exist in
  `queryregistry/`.

## What this layer IS NOT

- Not the canonical place for new query work.
- Not the right place to add naming aliases or dual-write compatibility.
- Not a long-term abstraction.

---

## Key files and entry points

- `server/registry/__init__.py` – legacy operation parsing and handler lookup.
- `server/registry/types.py` and `server/registry/models.py` – legacy request/response
  contracts.
- `server/registry/providers/` – legacy provider adapter hooks.

Adjacent guidance:
- `server/modules/AGENTS.md` for module lifecycle and runtime boundaries.
- `server/modules/providers/AGENTS.md` for DB provider behavior during migration.
- `queryregistry/AGENTS.md` for all new registry design and dispatch rules.

---

## Naming and schema conventions (when touching migration-only code)

- Keep SQL/object naming aligned with existing DB conventions:
  - `element_*` columns for metadata payloads.
  - `recid` as `bigint` for identifiers.
  - temporal metadata in `datetimeoffset` columns.
- Do not rename legacy operations to create compatibility layers; migrate callers to
  canonical `db:domain:subdomain:operation:version` ops in `queryregistry/`.

---

## Allowed changes in this directory

- Bug fixes required to keep currently unmigrated flows operational.
- Deletion/refactor work that removes legacy registry usage.
- Migration helpers that move domains to `queryregistry/` without introducing new
  aliases.

## Anti-patterns (forbidden)

- Adding new domain/subdomain handlers here.
- Introducing alias operations or compatibility wrappers.
- Adding fresh code paths that target legacy registry first.
- Preserving dead legacy code “just in case” after migration completes.

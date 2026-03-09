# Query Registry Mapping

This document summarizes the current query registry domains and how they map to
functional groupings described in the design discussion (content, identity,
system, finance). It reflects the **current code layout** under
`queryregistry/`.

## Functional groupings → query registry domains

### Content-related functions → `content`
Subdomains are stubbed and dispatch CRUD-style operations (`create/read/update/delete/list`).

- `content.assets`
- `content.galleries`
- `content.visibility`
- `content.moderation`
- `content.cache`

### Users, roles, and accounts data → `identity` + `system`
Role definitions and masks live in **system**, while role assignments live in
**identity**.

Identity subdomains (CRUD stubs):
- `identity.accounts`
- `identity.profiles`
- `identity.sessions`
- `identity.providers`
- `identity.audit`
- `identity.role_memberships` (assignments)

System subdomains (CRUD stubs, role definitions here):
- `system.roles` (role definitions + masks)

### System and security functionality → `system`
System subdomains are stubbed for CRUD operations unless noted.

- `system.config`
- `system.routes`
- `system.service_pages`
- `system.models`
- `system.personas`
- `system.public_vars` (read/list intended)
- `system.integrations`
- `system.roles`

### Finance and billing → `finance`
Finance currently exposes a status check service.

- `finance.check_status`

## Dispatch contract (authoritative)

All query registry operations MUST follow:

```
db:<domain>:<subdomain>:<operation>:<version>
```

This is the only supported dispatch format. Do not introduce alias or fallback
shim handlers for legacy or alternate operation shapes. When the contract must
change, prefer explicit breaking changes over compatibility debt.

Examples of currently scaffolded CRUD stubs:

- `db:content:assets:create:1`
- `db:identity:role_memberships:list:1`
- `db:system:roles:update:1`

## Handler entry points

- Root dispatch: `queryregistry/handler.py` → `queryregistry.handler.HANDLERS`
- Content: `queryregistry/content/handler.py`
- Identity: `queryregistry/identity/handler.py`
- System: `queryregistry/system/handler.py`
- Finance: `queryregistry/finance/handler.py`

## Current ownership map

| Domain | Subdomains | Query registry owner | Upstream module owners |
| --- | --- | --- | --- |
| `content` | `assets`, `galleries`, `visibility`, `moderation`, `cache` | `queryregistry/content/handler.py` | Content-facing modules that dispatch through the root registry handler |
| `identity` | `accounts`, `profiles`, `sessions`, `providers`, `audit`, `role_memberships` | `queryregistry/identity/handler.py` | Identity/auth modules, including role membership management flows |
| `system` | `config`, `routes`, `service_pages`, `models`, `personas`, `public_vars`, `integrations`, `roles` | `queryregistry/system/handler.py` | System/auth/admin modules |
| `finance` | `check_status` | `queryregistry/finance/handler.py` | Finance/status modules routed through the root registry handler |

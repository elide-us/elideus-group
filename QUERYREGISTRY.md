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
Finance currently exposes a legacy status check service.

- `finance.check_status` (legacy `queryregistry/finance` implementation)

## Legacy/transition domains

### `account`
The `account` domain remains in the tree and only implements a legacy
`check_status` handler. It does not yet follow the subdomain/CRUD stub
structure used by `content`, `identity`, and the expanded `system` domains.

## Dispatch shape (current)

Operations are expected to follow:

```
db:<domain>:<subdomain>:<operation>:<version>
```

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
- Account (legacy): `queryregistry/account/handler.py`

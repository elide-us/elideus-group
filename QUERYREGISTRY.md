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

## Migration notes: links + roles registry cutover

### Old → new handler mapping (with call chains)

| DB op(s) | Old handler | New handler | Call chain |
| --- | --- | --- | --- |
| `db:system:links:get_navbar_routes:1` | `server/registry/system/links/mssql.py:get_navbar_routes_v1` | `queryregistry/system/links/mssql.py:get_navbar_routes` | `rpc/public/links/services.py` → `server/modules/public_links_module.py` |
| `db:system:roles:list:1`, `db:system:roles:update:1`, `db:system:roles:delete:1` | `server/registry/system/roles/mssql.py` | `queryregistry/system/roles/mssql.py` | `server/modules/auth_module.py`, `server/modules/role_admin_module.py` |
| `db:system:roles:get_role_members:1`, `db:system:roles:get_role_non_members:1`, `db:system:roles:add_role_member:1`, `db:system:roles:remove_role_member:1` | `server/registry/system/roles/mssql.py:get_role_members_v1` / `get_role_non_members_v1` / `add_role_member_v1` / `remove_role_member_v1` | `queryregistry/identity/role_memberships/mssql.py:list_role_members` / `list_role_non_members` / `add_role_member` / `remove_role_member` | `server/modules/role_admin_module.py` via helper builders in `server/modules/registry/helpers.py` |

### Validation reminders

- NavBar route filtering uses `auth_ctx.role_mask` from the RPC layer, and the query registry `get_navbar_routes` handler filters using the `role_mask` supplied in the payload. Keep these data flow assumptions intact when removing the legacy registry modules.
- This migration assumes the legacy handlers are removed without aliasing or fallback shims once the query registry equivalents are live.

## OAuth provider coverage to reimplement

The legacy OAuth provider tests were removed while migrating to the query
registry. Reintroduce coverage that exercises the QueryRegistry-backed flows
end-to-end (RPC → service → module → query registry) once the new mocks are in
place:

- OAuth login and relink flows for `google`, `microsoft`, and `discord` using
  `db:identity:providers:relink:1` along with lookup operations for
  `get_by_provider_identifier` and `get_any_by_provider_identifier`.
- Email collision handling via `get_user_by_email` before `create_from_provider`.
- Profile refresh behavior (display name/email updates) after login.
- Profile image update/clear behavior after login.
- Microsoft home-account identifier fallback resolution.
- Google soft-undelete relink behavior.

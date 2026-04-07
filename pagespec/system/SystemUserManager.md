# User Manager

**Route:** `/user-manager`

*Replaces the former AccountRolesPage (`/account-roles`), AccountUsersPage (`/account-users`), AccountUserPanel (`/account-users/:guid`), and PublicProfile (`/profile/:guid`). Also subsumes the `support` domain's user and role management functionality into a unified page.*

## Tables Referenced

### `account_users`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, internal only — never exposed publicly |
| `element_public_id` | NVARCHAR(64) | Base64-encoded random GUID, unique, used for public profile URLs |
| `element_email` | NVARCHAR(1024) | User email |
| `element_display` | NVARCHAR(1024) | Display name |
| `element_optin` | BIT | Email display opt-in |
| `providers_recid` | BIGINT | FK → `auth_providers.recid`, default provider |
| `element_created_on` | DATETIMEOFFSET(7) | Account creation date |
| `element_modified_on` | DATETIMEOFFSET(7) | Last modified |

*`element_public_id` is generated once at account creation from a random GUID, base64-encoded. Not deterministic from and not reversible to `element_guid`. Public profile URLs use `/me/{public_profile_id}`. The internal `element_guid` is used in admin contexts only.*

### `users_roles`

| Column | Type | Notes |
|---|---|---|
| `users_guid` | UNIQUEIDENTIFIER | PK, FK → `account_users.element_guid` |
| `element_roles` | BIGINT | Role bitmask (being revamped — see Notes) |
| `element_created_on` | DATETIMEOFFSET(7) | |
| `element_modified_on` | DATETIMEOFFSET(7) | |

*Additional related tables (`users_credits`, `users_enablements`, `users_storage_cache`, `users_auth`, `users_profileimg`) are referenced for detail views but not detailed here — their schemas will be defined in subsequent specs.*

## Page Pattern: Summary + Headers + Detail

Follows the canonical summary + headers + detail pattern established by the Conversations page.

### Summary View

Aggregate telemetry across all users:
- Total user count
- Users with storage enabled
- Total credits in circulation
- Active sessions count
- Additional usage telemetry (TBD — registration trends, provider distribution, etc.)

### User Headers

Paginated list of user records showing key fields at a glance. Clicking a user drills into the detail view.

### User Detail

Selected user's account management panel:
- Display name (read-only for moderators, reset to "Default User" only — GDPR pattern)
- Public profile ID (read-only, displayed for reference)
- Email and opt-in status
- Credit balance (editable)
- Storage folder management
- **Role assignment** — mechanism TBD, the current bitmask model is being completely revamped. The page will support assigning and removing roles from a user regardless of the underlying implementation.
- Auth provider linkage summary
- Moderation flags and status

## Functions

### `readUserSummary`

- **Request:** none
- **Response:** `ReadUserSummaryResult1` — `{ total_users: int, storage_enabled_count: int, total_credits: int, active_sessions: int }`

### `readUserHeaders`

- **Request:** `ReadUserHeadersParams1` — `{ limit: int, offset: int }`
- **Response:** `ReadUserHeaderList1` — `{ elements: ReadUserHeaderElement1[] }`
- `ReadUserHeaderElement1` — `{ guid: string, public_id: string, display_name: string, email: string, provider_name: string, credits: int, role_count: int, is_storage_enabled: bool, created_on: string }`

### `readUserDetail`

- **Request:** `ReadUserDetailParams1` — `{ guid: string }`
- **Response:** `ReadUserDetailResult1` — `{ guid: string, public_id: string, display_name: string, email: string, optin: bool, provider_name: string, credits: int, roles: string[], is_storage_enabled: bool, auth_providers: string[], created_on: string, modified_on: string }`

### `resetUserDisplay`

- **Request:** `ResetUserDisplayParams1` — `{ guid: string }`
- **Response:** `ResetUserDisplayResult1` — `{ guid: string, display_name: string }`

*Resets display name to "Default User" — moderators cannot set arbitrary names (GDPR compliance).*

### `setUserCredits`

- **Request:** `SetUserCreditsParams1` — `{ guid: string, credits: int }`
- **Response:** `SetUserCreditsResult1` — `{ guid: string, credits: int }`

### `assignUserRole`

- **Request:** `AssignUserRoleParams1` — `{ guid: string, role: string }`
- **Response:** `AssignUserRoleResult1` — `{ guid: string, roles: string[] }`

### `removeUserRole`

- **Request:** `RemoveUserRoleParams1` — `{ guid: string, role: string }`
- **Response:** `RemoveUserRoleResult1` — `{ guid: string, roles: string[] }`

### `createUserStorageFolder`

- **Request:** `CreateUserStorageFolderParams1` — `{ guid: string }`
- **Response:** `CreateUserStorageFolderResult1` — `{ guid: string }`

## Public Profile Identity

The `element_public_id` on `account_users` is the **only** external-facing user identifier:
- Generated once at account creation from a random GUID, base64-encoded
- Not deterministic from and not reversible to the internal `element_guid`
- Public profile URLs: `/me/{public_profile_id}`
- All public API responses referencing users (gallery attribution, published files, etc.) use `public_id`
- The internal `element_guid` is visible in admin contexts (this page) but never in public-facing contexts
- Admin header and detail views include both `guid` (for admin operations) and `public_id` (for reference)

## GDPR Compliance

- Moderators **cannot edit** display names to arbitrary values. The only moderation action is resetting to the literal `"Default User"`.
- Role assignment/removal is an administrative action, not a moderation action — appropriate audit trails apply.
- User detail view is read-heavy with controlled write operations.

## Notes

- The **role assignment model is being completely revamped**. The current 64-bit bitmask (`users_roles.element_roles`) and `system_roles` lookup table will be replaced. The page spec defines role assignment abstractly (`assignUserRole`/`removeUserRole` by role name) — the underlying storage mechanism is not locked down here.
- The `support` RPC domain currently duplicates much of the `account` domain's functionality at a lower permission tier. In the rebuild, this consolidation means one page with permission-gated capabilities — what a moderator sees vs. what an admin sees is controlled by the role system, not by separate pages.
- Summary telemetry fields are intentionally underspecified — additional metrics will be defined as the platform matures.

## Description

Unified user administration page following the canonical summary + headers + detail pattern. Summary shows aggregate user telemetry. Headers list users with key fields (name, public ID, email, provider, credits, role count, storage status). Detail view provides account management: display name reset (GDPR-controlled), credit management, role assignment (mechanism TBD — bitmask being revamped), storage folder creation, and auth provider overview. Replaces three former pages and two RPC domains.
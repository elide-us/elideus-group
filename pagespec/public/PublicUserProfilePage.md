# User Profile

**Route:** `/me`

*Self-service profile management page for authenticated users. The user's central hub for account settings, shopping, credits, enablements, provider management, and account closure.*

*Public profiles are viewed at `/me/{public_profile_id}` where `public_profile_id` is a base64-encoded random GUID — not derived from or linked to the user's actual GUID except through the `account_users` table.*

## Page Sections

### Identity & Display

User's avatar, editable display name, email with opt-in toggle for public display. Profile image upload. Public profile link displayed for sharing.

### Credits & Enablements

Read-only display of current credit balance and reserve. List of active enablements showing what the user has purchased or been granted: storage access, adult content options, generation capabilities (video, TTS, text, images), and other service-tier features. Each enablement displayed as a status chip or toggle showing what's active.

### Shopping Cart & Wishlist

Cart component (TBD — shared with Products page) showing items the user has added for purchase. Wishlist for products the user is interested in but hasn't committed to. This is an alternate route to the purchase flow — the Products page is where items are browsed and added, this is where the cart lives alongside the user's account context.

### Provider Management

List of OAuth providers (Microsoft, Google, Discord, Apple) with per-provider status and controls:
- **Linked providers** show: provider name, the identity data associated with that provider (display name, email, avatar from that provider), and buttons for Unlink, Sync (refresh identity data without re-auth), and Set as Public Identity
- **Unlinked providers** show: provider name and a Link button
- **Set as public identity** button per linked provider — sets that provider's identity (name, avatar) as the user's public-facing profile on the site
- **Set as default** — designates which provider is used for login

All link/unlink/set-default actions require OAuth re-authentication with the target provider.

### Close Account

Separate clearly-marked section with:
- Explanation of what account closure means
- Note that provider identifiers are retained permanently to prevent account recreation abuse (anti-fraud)
- Note that no PII is retained — all user-controlled data is removed
- Link to the Privacy Policy page (`/pages/privacy-policy`)
- Close Account button with confirmation flow
- Unlinking the last provider is functionally equivalent to closing the account

## Tables Referenced

### `account_users`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, internal only — never exposed publicly |
| `element_public_id` | NVARCHAR(64) | Base64-encoded random GUID, unique, used for public profile URLs |
| `element_email` | NVARCHAR(1024) | User email |
| `element_display` | NVARCHAR(1024) | Display name |
| `element_optin` | BIT | Public email display opt-in |
| `providers_recid` | BIGINT | FK → `auth_providers.recid`, default provider |
| `element_created_on` | DATETIMEOFFSET(7) | |
| `element_modified_on` | DATETIMEOFFSET(7) | |

*`element_public_id` is generated once at account creation from a random GUID (not deterministic from `element_guid`). It serves as the only external-facing user identifier. The internal `element_guid` is never exposed in URLs or public API responses.*

### `users_auth`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `users_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `providers_recid` | BIGINT | FK → `auth_providers.recid` |
| `element_identifier` | UNIQUEIDENTIFIER | Provider-specific user ID, unique, **retained permanently** |
| `element_linked` | BIT | Active link status |
| `element_created_on` | DATETIMEOFFSET(7) | |
| `element_modified_on` | DATETIMEOFFSET(7) | |

### `users_credits`

| Column | Type | Notes |
|---|---|---|
| `users_guid` | UNIQUEIDENTIFIER | PK, FK → `account_users.element_guid` |
| `element_credits` | INT | Available credit balance |
| `element_reserve` | INT | Reserved credits (pending transactions), nullable |
| `element_created_on` | DATETIMEOFFSET(7) | |
| `element_modified_on` | DATETIMEOFFSET(7) | |

### `users_enablements`

| Column | Type | Notes |
|---|---|---|
| `users_guid` | UNIQUEIDENTIFIER | PK, FK → `account_users.element_guid` |
| `element_enablements` | NVARCHAR(MAX) | Enablement data (schema TBD — likely migrates to structured FK model) |
| `element_created_on` | DATETIMEOFFSET(7) | |
| `element_modified_on` | DATETIMEOFFSET(7) | |

*Enablements table will likely be redesigned from the current NVARCHAR(MAX) blob to a structured model — TBD alongside the role system revamp.*

## Functions

### `readProfile`

- **Request:** none (authenticated user context)
- **Response:** `ReadProfileResult1` — `{ public_id: string, display_name: string, email: string, optin: bool, default_provider: string, credits: int, reserve: int, profile_image: string | null, enablements: ReadProfileEnablementElement1[], auth_providers: ReadProfileProviderElement1[] }`
- `ReadProfileEnablementElement1` — `{ key: string, name: string, is_active: bool }`
- `ReadProfileProviderElement1` — `{ name: string, display: string, linked: bool, provider_display_name: string | null, provider_email: string | null, provider_avatar: string | null, is_default: bool, is_public_identity: bool }`

*Note: `public_id` is returned instead of `guid` — the internal GUID is never exposed.*

### `updateDisplayName`

- **Request:** `UpdateDisplayNameParams1` — `{ display_name: string }`
- **Response:** `UpdateDisplayNameResult1` — `{ display_name: string }`

### `updateEmailOptin`

- **Request:** `UpdateEmailOptinParams1` — `{ optin: bool }`
- **Response:** `UpdateEmailOptinResult1` — `{ optin: bool }`

### `updateProfileImage`

- **Request:** `UpdateProfileImageParams1` — `{ image: string }`
- **Response:** `UpdateProfileImageResult1` — `{ profile_image: string }`

### `setDefaultProvider`

- **Request:** `SetDefaultProviderParams1` — `{ provider: string, code: string | null, id_token: string | null, access_token: string | null }`
- **Response:** `SetDefaultProviderResult1` — `{ provider: string }`

### `setPublicIdentity`

- **Request:** `SetPublicIdentityParams1` — `{ provider: string }`
- **Response:** `SetPublicIdentityResult1` — `{ provider: string }`

### `syncProvider`

- **Request:** `SyncProviderParams1` — `{ provider: string }`
- **Response:** `SyncProviderResult1` — `{ provider: string, provider_display_name: string | null, provider_email: string | null, provider_avatar: string | null }`

### `linkProvider`

- **Request:** `LinkProviderParams1` — `{ provider: string, code: string | null, id_token: string | null, access_token: string | null }`
- **Response:** `LinkProviderResult1` — `{ provider: string }`

### `unlinkProvider`

- **Request:** `UnlinkProviderParams1` — `{ provider: string, new_default: string | null }`
- **Response:** `UnlinkProviderResult1` — `{ provider: string }`

### `closeAccount`

- **Request:** `CloseAccountParams1` — `{ confirm: bool }`
- **Response:** `CloseAccountResult1` — `{ closed: bool }`

### `readCart`

- **Request:** none
- **Response:** `ReadCartResult1` — `{ elements: ReadCartElement1[] }`
- `ReadCartElement1` — `{ recid: int, product_sku: string, product_name: string, currency_price: string, credit_price: int, quantity: int }`

### `readWishlist`

- **Request:** none
- **Response:** `ReadWishlistResult1` — `{ elements: ReadWishlistElement1[] }`
- `ReadWishlistElement1` — `{ recid: int, product_sku: string, product_name: string, currency_price: string, credit_price: int }`

*Cart and wishlist function signatures TBD — depends on cart component design.*

## Public Profile Identity

The `element_public_id` column on `account_users` is the **only** external-facing user identifier:
- Generated once at account creation from a random GUID, base64-encoded
- Not deterministic from and not reversible to the internal `element_guid`
- Used in public profile URLs: `/me/{public_profile_id}`
- Used in any API response that references a user publicly (gallery attribution, published files, etc.)
- The internal `element_guid` is never exposed in URLs, public API responses, or client-side code outside of admin contexts

This requirement also applies to the User Manager page — admin views may display the internal GUID for administrative purposes, but public-facing references always use `element_public_id`.

## Notes

- All self-service functions operate on the authenticated user's own account — no GUID or public_id parameter needed.
- Provider link/unlink/set-default require OAuth re-authentication flows. Sync does not.
- Cart and wishlist are new features — table schemas and full function signatures TBD pending cart component design.
- Enablements will likely be redesigned from NVARCHAR(MAX) blob to structured model alongside role revamp.
- Close Account is explicit and separate from last-provider-unlink, though both lead to the same result.

## Description

Self-service profile hub at `/me`. Sections: identity and display name management, credit balance and enablements overview, shopping cart and wishlist (shared cart component with Products page), OAuth provider management with link/unlink/sync/set-public-identity controls, and account closure with privacy policy context. Public profiles are accessible at `/me/{public_profile_id}`. All user data is fully user-controlled. Uses the application theme and shared form controls.
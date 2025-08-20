# Security Roles

This project uses a signed 64‑bit integer to represent security roles
and user feature flags. Bit 63 is unused to avoid the sign bit. The
high bits define system roles and the low bits are used for user level
flags.

## Role Bit Assignments

| Bit | Hex Value             | Role Name                 | Notes |
|----:|----------------------:|---------------------------|------|
| 62  | `0x4000000000000000`  | `ROLE_SERVICE_ADMIN`      | The configuration of the service, such as API keys |
| 61  | `0x2000000000000000`  | `ROLE_SYSTEM_ADMIN`       | Access to system configuration features |
| 60  | `0x1000000000000000`  | `ROLE_ACCOUNT_ADMIN`      | Manage security role definitions and user assignments |
| 59  | `0x0800000000000000`  | `ROLE_MODERATOR`          | Access to moderation tools |
| 58  | `0x0400000000000000`  | `ROLE_SUPPORT`            | Access to support utilities |
| 57  | `0x0200000000000000`  | *(reserved)*              | |
| 56  | `0x0100000000000000`  | *(reserved)*              | |
| ... | ...                   |                           | |
| 6   | `0x0000000000000040`  | `ROLE_DISCORD_BOT`        | Allows the user to interact with the system via Discord |
| 5   | `0x0000000000000020`  | `ROLE_LUMAAI_VIDEO`       | Allows the user to generate videos with LumaLabs AI |
| 4   | `0x0000000000000010`  | `ROLE_OPENAI_TEXT`        | Allows the user to generate text with OpenAI |
| 3   | `0x0000000000000008`  | `ROLE_OPENAI_TTS`         | Allows the user to generate TTS with OpenAI |
| 2   | `0x0000000000000004`  | `ROLE_OPENAI_IMAGE`       | Allows the user to generate images with OpenAI |
| 1   | `0x0000000000000002`  | `ROLE_STORAGE`            | Allows access to the storage domain |
| 0   | `0x0000000000000001`  | `ROLE_REGISTERED`         | Grants access to profile and provider management |

## Role Macros

`ROLE_GLOBAL_ADMIN = ROLE_SERVICE_ADMIN | ROLE_SYSTEM_ADMIN | ROLE_MODERATION | ROLE_SUPPORT`
`ROLE_SERVICE_AGENT = ROLE_MODERATION | ROLE_SUPPORT`

## Authentication Domains

Understanding the various authentication domains and where values are used and stored is vital to the stability of the application.

### Provider Domain

The authentication provider is a client-side domain, this is the data that the client provides to the application via libraries such as the MSAL that provides a private client for the user to obtain a security token to validate their identity against public well-known JWKS. There are four pieces of data from the provide that are passed to the app:

1) User's unique identifier
2) User's email address or primary username
3) User's profile image
4) User's display name

### Application Domain

 This is the user's local session on a given device. This session includes a bearer token which identifies the unique session and device that is being handled by the back end. When a user makes a request (via app, discord, api, mcp) their bearer token is decoded and security is looked up in the back end for the user, if authorized, the RPC transaction will then continue forward. The client retains only this bearer token which contains only arbitrary internal data such as the user's randomly assigned GUID, no personal details should be included in this token.

 ### Server Domain

 This is the back end server which handles all requests. The server domain includes the database and the information that is retained in the database is as follows:

 1) User's unique account identifier
 2) User's email address*
 3) User's unique session and device identifier
 4) User's profile image (if available)

 Email Opt-Out: If the user opt out of email, they will not be sent any e-mail based communication and their email address will not be shown to other users in their public profile.
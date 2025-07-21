

63 0x4000 0000 0000 0000  ROLE_SERVICE_ADMIN        Access to urn:service:(config | vars) namespace
62 0x2000 0000 0000 0000  ROLE_SYSTEM_ADMIN         Access to urn:system namespace
61 0x1000 0000 0000 0000  ROLE_MODERATOR            Access to urn:moderator namespace
60 0x0800 0000 0000 0000  ROLE_SUPPORT              Access to urn:support namespace

## Combined User Role Examples
ROLE_GLOBAL_ADMIN = ROLE_SERVICE_ADMIN | ROLE_SYSTEM_ADMIN | ROLE_MODERATOR | ROLE_SUPPORT
ROLE_SERVICE_AGENT = ROLE_MODERATOR | ROLE_SUPPORT

 1 0x0000 0000 0000 0001  USER_LOGGED_IN            Filter for public links and routes
 2 0x0000 0000 0000 0002  USER_API_ALLOWED          Allow REST API access for user
 3 0x0000 0000 0000 0004  USER_DISCORD_ALLOWED      Allow Discord bot access for user
 4 0x0000 0000 0000 0008  USER_SOCIAL_ALLOWED       Allow Social posting

## Basic User Feature Enablement
USER_ENABLEMENT_AUTOMATION = USER_API_ALLOWED | USER_SOCIAL_ALLOWED
USER_ENABLEMENT_INTERACTIVE = USER_DISCORD_ALLOWED | USER_SOCIAL_ALLOWED
USER_ENABLEMENT_PREMIUM = USER_API_ALLOWED | USER_DISCORD_ALLOWED | USER_SOCIAL_ALLOWED


33 0x0000 0001 0000 0000  CAP_CALL_WEB              RPC can be called from React frontend
34 0x0000 0002 0000 0000  CAP_CALL_DISCORD          RPC can be called from Discord
35 0x0000 0004 0000 0000  CAP_CALL_API              PRC can be called through REST API

 1 0x0000 0000 0000 0001  CAP_RESP_TYPED            Default RPCResponse for React frontend
 2 0x0000 0000 0000 0002  CAP_RESP_DISCORD          Reponse formatted for Discord message shape
 3 0x0000 0000 0000 0004  CAP_RESP_API              Untyped raw JSON (public API style)
 4 0x0000 0000 0000 0008  CAP_RESP_BSKY             Response formatted for Bluesky message shape

## A RPC call capability filter to allow input from React or Discord and output to React, Discord, or Bluesky
CAPABILITY_VERSION_REPORTING = CAP_CALL_WEB | CAP_CALL| DISCORD | CAP_REP_TYPED | CAP_RESP_DISCORD | CAP_RESP_BSKY













🔐 SECURITY.md — Access Roles, Feature Enablement & RPC Capability Filtering
This document outlines the 64-bit bitmask strategy used to enforce security, interface-level enablement, and RPC call routing permissions within the system. All interactions are evaluated through one or more of the following masks:

🧱 Security Roles (Bits 61–64)
These bits define system-level trust and access within internal namespaces.

Bit	Hex Mask	Role Name	Description
63      0x4000000000000000      ROLE_SERVICE_ADMIN	Grants access to urn:service:* namespace including secrets/config
62      0x2000000000000000      ROLE_SYSTEM_ADMIN	Grants access to urn:system:* (admin panels, orchestration, audits)
61      0x1000000000000000      ROLE_MODERATOR	    Grants access to urn:moderator:* (content and abuse queues)
60      0x0800000000000000      ROLE_SUPPORT	    Grants access to urn:support:* (user impersonation, account adjustments)

👥 Role Combinations
ROLE_GLOBAL_ADMIN   = ROLE_SERVICE_ADMIN | ROLE_SYSTEM_ADMIN | ROLE_MODERATOR | ROLE_SUPPORT
ROLE_SERVICE_AGENT  = ROLE_MODERATOR | ROLE_SUPPORT

🔓 User Enablement Flags (Bits 1–4)
These bits are user-specific flags to control interface access per user.

Bit	Hex Mask	Flag Name	Description
1	0x0000000000000001	USER_LOGGED_IN	    User has authenticated; unlocks non-public routes
2	0x0000000000000002	USER_API_ALLOWED	    User can access public REST API endpoints
3	0x0000000000000004	USER_DISCORD_ALLOWED	User can interact with the system via Discord bot
4	0x0000000000000008	USER_SOCIAL_ALLOWED	    User can post results to social media (e.g., Bluesky, Threads)

🧩 Feature Enablement Macros
USER_ENABLEMENT_AUTOMATION  = USER_API_ALLOWED | USER_SOCIAL_ALLOWED
USER_ENABLEMENT_INTERACTIVE = USER_DISCORD_ALLOWED | USER_SOCIAL_ALLOWED
USER_ENABLEMENT_PREMIUM     = USER_API_ALLOWED | USER_DISCORD_ALLOWED | USER_SOCIAL_ALLOWED

📡 RPC Capability Mask (64-bit)
This bitmask is used on each RPC method definition to enforce where it can be called from and how the response is formatted.

It is split as follows:

Bits 0–31 – Response formats
Bits 32–63 – Callable sources

🔽 Bits 33–35: Callable Origins
Bit	Hex Mask	Flag Name	Description
33	0x0000000100000000	CAP_CALL_WEB	RPC callable via React frontend
34	0x0000000200000000	CAP_CALL_DISCORD	RPC callable from Discord bot
35	0x0000000400000000	CAP_CALL_API	RPC callable from REST API endpoint
34  0x0000000800000000  **Future Expansion**

🔼 Bits 1–4: Response Targets
Bit	Hex Mask	Flag Name	Description
1	0x0000000000000001	CAP_RESP_TYPED	Typed RPCResponse, intended for React
2	0x0000000000000002	CAP_RESP_DISCORD	Discord-structured message response
3	0x0000000000000004	CAP_RESP_API	Untyped JSON response for public API
4	0x0000000000000008	CAP_RESP_BSKY	Social-media message (Bluesky, Threads, etc.)
5   0x0000000000000010  **Future Expansion**

🧪 Example: Capability Combo
// This method can be called from frontend or Discord,
// and respond to frontend, Discord, or Bluesky formats:
CAPABILITY_VERSION_REPORTING =
    CAP_CALL_WEB |
    CAP_CALL_DISCORD |
    CAP_RESP_TYPED |
    CAP_RESP_DISCORD |
    CAP_RESP_BSKY;

// Hex: 0x000000030000000B
🔐 Runtime Filtering Logic
Each RPC call is filtered through:

Security Role Mask – Do you have the right to enter this namespace?

User Capability Mask – Are you permitted to use this interface?

RPC Capability Mask – Is this RPC method callable from here, and can it respond where it’s going?
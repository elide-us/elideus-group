# Authentication Workflow Diagrams

This document captures the authentication workflows in layered diagrams. Each workflow is shown with a layered architecture view and per-layer sequence diagrams that stop at provider contracts.

## Session Token Issuance (`auth.session.get_token`)

### Layered Architecture
```mermaid
flowchart LR
  Client[Client Application]
  RPCService[RPC auth.session.get_token]
  SessionModule[SessionModule]
  AuthModule[AuthModule]
  OauthModule[OauthModule]
  DbModule[DbModule]
  AuthProvider[AuthProviderBase Contract]
  DbProvider[DbProviderBase Contract]

  Client --> RPCService
  RPCService --> SessionModule
  SessionModule --> AuthModule
  SessionModule --> OauthModule
  AuthModule --> AuthProvider
  OauthModule --> DbModule
  DbModule --> DbProvider
```

### RPC Layer Sequence
```mermaid
sequenceDiagram
  participant Client
  participant FastAPI as FastAPI RPC Router
  participant Service as auth.session.get_token Service

  Client->>FastAPI: POST /rpc/auth/session/get_token
  FastAPI->>Service: Dispatch request body & headers
  Service->>Service: Validate provider, tokens, fingerprint
  Service->>FastAPI: RPCResponse with session token & profile
  FastAPI-->>Client: JSON response + rotation cookie
```

### Server Module Layer Sequence
```mermaid
sequenceDiagram
  participant RPC as RPC Service
  participant Session as SessionModule
  participant Auth as AuthModule
  participant Oauth as OauthModule
  participant DB as DbModule

  RPC->>Session: issue_token(provider, tokens, fingerprint)
  Session->>Auth: handle_auth_login(provider, id_token, access_token)
  Auth->>Auth: Resolve provider strategy & validate via contract
  Auth-->>Session: GUID, profile, token payload
  Session->>Oauth: resolve_user(...)
  Oauth->>DB: run(create_from_provider / link / relink)
  DB-->>Oauth: User record
  Oauth->>DB: run(set_rotkey)
  Oauth->>DB: run(create_session)
  Oauth->>DB: run(update_device_token)
  Oauth-->>Session: session_token, rotation_token, expirations
  Session-->>RPC: token + profile payload
```

### Provider Layer Sequence
```mermaid
sequenceDiagram
  participant Auth as AuthModule
  participant AuthProvider as AuthProviderBase
  participant Oauth as OauthModule
  participant DbModule as DbModule
  participant DbProvider as DbProviderBase

  Auth->>AuthProvider: verify_id_token(id_token, access_token)
  AuthProvider-->>Auth: token payload
  Auth->>AuthProvider: fetch_user_profile(access_token)
  AuthProvider-->>Auth: provider profile
  Oauth->>DbModule: run(set_rotkey_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: DBResponse
  Oauth->>DbModule: run(create_session_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Session record
  Oauth->>DbModule: run(update_device_token_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Confirmation
```

## Session Token Refresh (`auth.session.refresh_token`)

### Layered Architecture
```mermaid
flowchart LR
  Client[Client Application]
  RPCService[RPC auth.session.refresh_token]
  SessionModule[SessionModule]
  AuthModule[AuthModule]
  DbModule[DbModule]
  DbProvider[DbProviderBase Contract]

  Client --> RPCService
  RPCService --> SessionModule
  SessionModule --> AuthModule
  SessionModule --> DbModule
  DbModule --> DbProvider
```

### RPC Layer Sequence
```mermaid
sequenceDiagram
  participant Client
  participant FastAPI as FastAPI RPC Router
  participant Service as auth.session.refresh_token Service

  Client->>FastAPI: POST /rpc/auth/session/refresh_token
  FastAPI->>Service: Dispatch rotation cookie & payload
  Service->>Service: Validate rotation token & fingerprint
  Service-->>FastAPI: RPCResponse with new session token
  FastAPI-->>Client: JSON response
```

### Server Module Layer Sequence
```mermaid
sequenceDiagram
  participant RPC as RPC Service
  participant Session as SessionModule
  participant Auth as AuthModule
  participant DB as DbModule
  participant Query as QueryRegistry

  RPC->>Session: refresh_token(rotation_token, fingerprint)
  Session->>Auth: decode_rotation_token(rotation_token)
  Auth-->>Session: GUID from rotation token
  Session->>Query: dispatch_query_request(get_rotkey_request)
  Query-->>Session: Stored rotation key & provider
  Session->>Auth: get_user_roles(guid)
  Auth-->>Session: Role names & mask
  Session->>DB: run(create_session_request)
  DB-->>Session: Session GUID & device GUID
  Session->>Auth: make_session_token(...)
  Auth-->>Session: New session token
  Session->>DB: run(update_device_token_request)
  DB-->>Session: Confirmation
  Session-->>RPC: Session token payload
```

### Provider Layer Sequence
```mermaid
sequenceDiagram
  participant Session as SessionModule
  participant DbModule as DbModule
  participant DbProvider as DbProviderBase
  participant Query as QueryRegistry

  Session->>Query: dispatch_query_request(get_rotkey_request)
  Query-->>Session: DBResponse with rotation key
  Session->>DbModule: run(create_session_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Session details
  Session->>DbModule: run(update_device_token_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Confirmation
```

## Session Invalidation (`auth.session.invalidate_token`)

### Layered Architecture
```mermaid
flowchart LR
  Client[Client Application]
  RPCService[RPC auth.session.invalidate_token]
  SessionModule[SessionModule]
  DbModule[DbModule]
  DbProvider[DbProviderBase Contract]

  Client --> RPCService
  RPCService --> SessionModule
  SessionModule --> DbModule
  DbModule --> DbProvider
```

### RPC Layer Sequence
```mermaid
sequenceDiagram
  participant Client
  participant FastAPI as FastAPI RPC Router
  participant Service as auth.session.invalidate_token Service

  Client->>FastAPI: POST /rpc/auth/session/invalidate_token
  FastAPI->>Service: Forward RPC request & auth context
  Service->>Service: Ensure session token authenticated
  Service-->>FastAPI: RPCResponse ok
  FastAPI-->>Client: JSON { ok: true }
```

### Server Module Layer Sequence
```mermaid
sequenceDiagram
  participant RPC as RPC Service
  participant Session as SessionModule
  participant DB as DbModule

  RPC->>Session: invalidate_token()
  Session->>DB: run(set_rotkey_request with empty rotkey)
  DB-->>Session: Confirmation
  Session-->>RPC: ok payload
```

### Provider Layer Sequence
```mermaid
sequenceDiagram
  participant Session as SessionModule
  participant DbModule as DbModule
  participant DbProvider as DbProviderBase

  Session->>DbModule: run(set_rotkey_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Confirmation
```

## Device Logout (`auth.session.logout_device`)

### Layered Architecture
```mermaid
flowchart LR
  Client[Client Application]
  RPCService[RPC auth.session.logout_device]
  SessionModule[SessionModule]
  DbModule[DbModule]
  DbProvider[DbProviderBase Contract]

  Client --> RPCService
  RPCService --> SessionModule
  SessionModule --> DbModule
  DbModule --> DbProvider
```

### RPC Layer Sequence
```mermaid
sequenceDiagram
  participant Client
  participant FastAPI as FastAPI RPC Router
  participant Service as auth.session.logout_device Service

  Client->>FastAPI: POST /rpc/auth/session/logout_device (Authorization: Bearer)
  FastAPI->>Service: Dispatch token & request metadata
  Service->>Service: Validate bearer token presence
  Service-->>FastAPI: RPCResponse ok
  FastAPI-->>Client: JSON { ok: true }
```

### Server Module Layer Sequence
```mermaid
sequenceDiagram
  participant RPC as RPC Service
  participant Session as SessionModule
  participant DB as DbModule

  RPC->>Session: logout_device(bearer token)
  Session->>DB: run(revoke_device_token_request(access_token))
  DB-->>Session: Confirmation
  Session-->>RPC: ok payload
```

### Provider Layer Sequence
```mermaid
sequenceDiagram
  participant Session as SessionModule
  participant DbModule as DbModule
  participant DbProvider as DbProviderBase

  Session->>DbModule: run(revoke_device_token_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Confirmation
```

## Session Inspection (`auth.session.get_session`)

### Layered Architecture
```mermaid
flowchart LR
  Client[Client Application]
  RPCService[RPC auth.session.get_session]
  SessionModule[SessionModule]
  DbModule[DbModule]
  DbProvider[DbProviderBase Contract]

  Client --> RPCService
  RPCService --> SessionModule
  SessionModule --> DbModule
  DbModule --> DbProvider
```

### RPC Layer Sequence
```mermaid
sequenceDiagram
  participant Client
  participant FastAPI as FastAPI RPC Router
  participant Service as auth.session.get_session Service

  Client->>FastAPI: POST /rpc/auth/session/get_session (Authorization: Bearer)
  FastAPI->>Service: Forward token, headers, client info
  Service->>Service: Validate bearer token presence
  Service-->>FastAPI: RPCResponse with session payload
  FastAPI-->>Client: JSON session details
```

### Server Module Layer Sequence
```mermaid
sequenceDiagram
  participant RPC as RPC Service
  participant Session as SessionModule
  participant DB as DbModule

  RPC->>Session: get_session(bearer token)
  Session->>DB: run(db:account:session:get_by_access_token)
  DB-->>Session: Session record
  Session->>Session: Verify revocation & expiration
  Session->>DB: run(update_session_request)
  DB-->>Session: Confirmation (best effort)
  Session-->>RPC: Session metadata payload
```

### Provider Layer Sequence
```mermaid
sequenceDiagram
  participant Session as SessionModule
  participant DbModule as DbModule
  participant DbProvider as DbProviderBase

  Session->>DbModule: run(get_by_access_token request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Session record
  Session->>DbModule: run(update_session_request)
  DbModule->>DbProvider: run(DBRequest)
  DbProvider-->>DbModule: Confirmation
```

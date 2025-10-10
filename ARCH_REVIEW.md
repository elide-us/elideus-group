# Architecture Review Summary

This document captures the current state of the rebuild, highlights where the
implementation already matches the architectural goals, and enumerates follow-up
items that keep the vision intact as the product surface expands. The review is
based on the runtime entry point (`main.py`), the RPC and module layers, and the
registry/provider implementations that back each contract.

## Layered Architecture

* FastAPI exposes a single ingress at `/rpc`. The `rpc.handler.handle_rpc_request`
  helper unwraps the request, enforces URN structure, and dispatches the domain
  handler without introducing business logic at the boundary. The handler
  propagates the `request_id` through the async context for end-to-end
  correlation.
* RPC domain packages (for example `rpc.service`, `rpc.system`, `rpc.users`)
  translate URN invocations into service calls. They never reach into modules or
  providers directly; instead they rely on service facades registered during
  module initialization.
* Modules are instantiated automatically by `ModuleManager`. Each module is a
  `BaseModule` subclass that performs two-phase bootstrapping (`startup()` and
  `mark_ready()`) and publishes an RPC-safe facade via `create_service()`. The
  runtime binds these facades to `app.state.services` so RPC handlers always go
  through the approved abstraction.
* Providers live under `server/modules/providers`. Database providers expose a
  strict `run(op, args)` contract while auth providers expose
  `verify_id_token/access_token` helpers. Providers are loaded and verified by
  the registry before they are marked ready, preventing partial coverage.

## Security Controls

* `AuthModule` exposes a facade that resolves capability masks and performs
  authorization checks with `user_has_role`. RPC handlers call these helpers
  before invoking business logic so capabilities are enforced at the service
  boundary and modules can assume pre-validated callers.
* Role bit assignments are centrally defined in `ARCHITECTURE.md`. The auth
  facade retrieves the expected role mask by name and raises a structured
  `rpc.role.undefined` error when contracts reference an unconfigured
  capability. This fail-fast behavior keeps privilege mapping auditable.
* Role definition management lives under the `service.roles` namespace and
  requires `ROLE_SERVICE_ADMIN`, preserving a separation from account
  administration. `account.role.*` operations focus solely on safe assignment
  workflows behind `ROLE_ACCOUNT_ADMIN`.
* All ingress paths require bearer tokens with the exception of the `auth.*` and
  `public.*` domains. Tokens are validated against provider JWKS caches, which
  are refreshed on demand and never persist outside the auth provider scope.

## Registry and Provider Bindings

* Registry routes pair each `db:` contract with a provider map and descriptor
  metadata during registration. Provider modules cannot mark themselves ready
  until `verify_provider_coverage()` confirms that every declared contract has a
  callable implementation.
* Database providers translate `DbRunMode` enumerations into concrete cursor
  behavior. Results are marshalled into the canonical `DBResult` model so
  callers always receive deterministic payloads (`rows`, `rowcount`, optional
  JSON projections).
* Providers implement `LifecycleProvider.startup()` and `.shutdown()` to manage
  external connections (for example, HTTP clients or database pools). Startup
  failures propagate as module initialization errors, preventing half-initialized
  services from accepting traffic.

## Contracts and Models

* RPC contracts follow the `urn:domain:subdomain:function:vX` convention. The
  dispatcher rejects malformed URNs or unknown domains before any module logic
  is executed, guaranteeing deterministic routing.
* Request payloads are unpacked into `server.models.RPCRequest` and validated
  against Pydantic models defined alongside each RPC service. Responses are
  serialized by `RPCResponse`, which enforces explicit success/error payloads.
* Database operations return strongly typed `DBResult` objects. Modules map
  these into domain models before exposing them to RPC services, keeping raw
  provider structures from leaking into higher layers.

## Error Handling and Telemetry

* The shared `server.errors` helper defines canonical factory functions for RPC
  error codes (`bad_request`, `forbidden`, `service_unavailable`, and so forth).
  RPC handlers convert these into `HTTPException` instances while preserving the
  diagnostic string for operators.
* `rpc.handler._dispatch_rpc_request` captures all `RPCServiceError` and
  `HTTPException` instances, re-wraps them when necessary, and logs failures at
  `ERROR` level with the correlated request ID. Unhandled exceptions bubble up
  to FastAPI, where `main.py` logs the stack trace before returning a generic
  `500` response.
* `server.helpers.logging` centralizes root logger configuration. Request flows
  default to INFO-level audit logs with optional DEBUG output gated behind an
  environment-controlled logging level. Discord log forwarding now emits warning
  messages instead of silently suppressing transport issues, preserving the
  "fail secure" philosophy.

## Fail-Safe Defaults

* Module startup aborts the application when dependencies fail to initialize,
  preventing degraded providers from serving stale or partial data.
* Registry verification occurs before modules call `mark_ready()`, so RPC
  handlers can safely block on `await on_ready()` without race conditions.
* Authentication providers validate JWKS caches before accepting tokens and
  reject anything with missing keys, expired signatures, or claim mismatches.

## Follow-Up Checklist

* [ ] Review modules that catch broad `Exception` instances and log diagnostic
  metadata to avoid silent suppression of actionable failures.
* [ ] Expand automated tests that exercise registry/provider wiring to detect
  schema drift earlier in CI.
* [ ] Continue documenting RPC contracts in `RPC.md` as new domains ship so the
  service layer remains discoverable for frontend consumers.

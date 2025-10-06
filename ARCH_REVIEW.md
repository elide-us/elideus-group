# Architecture Review Summary

## RPC Ingress

* All external RPC traffic terminates at the FastAPI router mounted on `/rpc`. No other ingress paths are permitted for RPC contracts.
* The router delegates to `rpc.handler.handle_rpc_request`, which validates URN syntax and rejects unknown namespaces before module logic executes.

## Authentication and Capability Enforcement

* `resolve_required_mask` resolves role bitmasks through the `AuthService` and raises `rpc.role.undefined` if a capability name is missing.
* RPC domain handlers (for example the Service domain) call `user_has_role` before invoking subdomain handlers. Calls short-circuit with `403 Forbidden` when the caller is not authorized, ensuring downstream modules cannot bypass capability checks.

## Registry and Provider Bindings

* Registry routes pair each `db:` contract with a provider map and optional descriptor metadata when they are registered.
* Loading a provider module hydrates callable implementations for every contract. `RegistryRouter.verify_provider_coverage()` fails start-up if any mapping is missing, preventing partially wired providers from serving traffic.

## Structured Logging

* `request_id` values are propagated through async context variables so every log entry related to a request can be correlated.
* Security audit logs record the RPC operation, caller identity source, and authorization status for Discord, MTLS, and bearer token flows.

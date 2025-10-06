# Registry Implementation Plan

## 1. Role in the request pipeline
The registry is the bridging layer between the DB module and the provider-specific
query stores. The intended request path will be:

```
Frontend → RPC handler → module method → DbModule.run() → Registry → provider map → provider backend
```

* **RPC layer** keeps transport logic and security checks thin.
* **Modules** (for example `StorageModule`) translate business tasks into
  database operations and work with strongly-typed request/response models.
* **DbModule** converts a module call into a `db:` registry key and forwards the
  request payload.
* **Registry** resolves that key to a domain/subdomain/function triple and
  selects the appropriate provider implementation.
* **Provider map** finds the concrete database flavour implementation
  (`mssql`, `postgres`, `mysql`, …) and executes the stored query.
* **Provider backend** executes SQL (or other driver specific logic) and
  returns raw rows that the DbModule normalises into structured responses.

## 2. Request/response contract
Today the DB module already passes dictionaries around and produces `DBResult`
objects. We will tighten this contract so that every call uses explicit models:

* `DBRequest`: immutable Pydantic model with the fields `op: str`,
  `params: dict[str, Any]`, and optional metadata (calling module, timeout,
  tracing IDs). This replaces the implicit `(op, dict)` tuple in
  `DbModule.run`.
* `DBResponse`: wrapper around the existing `DBResult` that always contains the
  provider’s `rows`, `rowcount`, and optional `meta` (execution time, warnings).
  Internally we can continue to reuse `DBResult` until the rename is complete,
  but the registry interface will consistently speak in terms of
  request/response objects.

The DbModule will be responsible for:

1. Constructing `DBRequest` from the module call.
2. Dispatching the request into the registry.
3. Converting the resulting `DBResponse` back into module-friendly data.

## 3. Domain layout and storage mapping
`server/registry` mirrors the `db:` namespace. After the consolidation the top
level is organised around the `system`, `users`, and `finance` domains:

```
server/registry/
  finance/
    credits/
      __init__.py
      mssql.py
  providers/
  system/
    assistant/
      conversations/
      models/
      personas/
    config/
    public/
      links/
      vars/
    roles/
    routes/
  users/
    content/
      cache/
      files/
      public/
    profile/
    public/
      users/
    security/
      accounts/
      identities/
      oauth/
      sessions/
```

* **System domain** centralises global metadata such as assistant
  conversations/models/personas, runtime configuration, public navigation data,
  and role/route registries. Subdomains use dotted names (`assistant.conversations`,
  `public.links`, …) so the generated URNs follow the
  `db:system:{subdomain}:{operation}:{version}` pattern.
* **Users domain** contains user-scoped behaviour. Content storage helpers,
  public profile lookups, and security/authentication flows now live under the
  `db:users:*` namespace with dotted subdomains like
  `content.cache` or `security.sessions`.
* **Finance domain** captures billing-related operations. Today it exposes the
  credits writer under `db:finance:credits:set:1`.

Representative URNs:

| Registry key | Target module | Notes |
| --- | --- | --- |
| `db:system:assistant.conversations:insert:1` | `system.assistant.conversations` | Persists assistant conversation transcripts. |
| `db:system:assistant.models:list:1` | `system.assistant.models` | Lists configured LLM backends. |
| `db:system:public.links:get_navbar_routes:1` | `system.public.links` | Provides navigation metadata for the UI shell. |
| `db:system:public.vars:get_version:1` | `system.public.vars` | Reports service version/host metadata. |
| `db:users:content.cache:list:1` | `users.content.cache` | Fetches cached storage items for a user. |
| `db:users:content.public:get_public_files:1` | `users.content.public` | Returns public gallery entries. |
| `db:users:content.files:set_gallery:1` | `users.content.files` | Toggles gallery status for a file. |
| `db:users:public.users:get_published_files:1` | `users.public.users` | Exposes public profile assets. |
| `db:users:security.accounts:get_security_profile:1` | `users.security.accounts` | Primary security/profile view. |
| `db:users:security.sessions:create_session:1` | `users.security.sessions` | Issues a new session + device token. |
| `db:finance:credits:set:1` | `finance.credits` | Writes billing credit balances. |

Legacy `db:assistant:*`, `db:content:*`, `db:public:*`, and `db:security:*`
namespaces have been folded into the consolidated layout above. Modules now call
the `db:system:*`, `db:users:*`, or `db:finance:*` URNs directly via the registry.

## 4. Registry module contract
Each domain package will provide a `register(registry: RegistryRouter)` function
that registers its submodules. The implementation shape:

```python
# server/registry/users/__init__.py
from . import content, profile, public, security


def register(registry: RegistryRouter) -> None:
  domain = registry.domain("users")
  content.register(domain)
  profile.register(domain.subdomain("profile"))
  public.register(domain)
  security.register(domain)
```

Each subdomain exposes a `register` helper that wires its functions to the
provider map. Aggregators such as `users/content/__init__.py` translate dotted
subdomain names into the correct `SubdomainRouter`:

```python
# server/registry/users/content/__init__.py
from . import cache, files, public


def register(domain: DomainRouter) -> None:
  cache.register(domain.subdomain("content.cache"))
  files.register(domain.subdomain("content.files"))
  public.register(domain.subdomain("content.public"))
```

Leaf modules (`users/content/cache/__init__.py`,
`users/content/cache/mssql.py`, …) define their `db:` functions using
`SubdomainRouter.add_function`. By default the router derives the provider map
(`"{domain}.{subdomain}.{name}"`) and MSSQL binding
(`"server.registry.{domain}.{subdomain}.mssql", "{name}_v{version}"`). When a
provider uses a descriptive name you can supply an `implementation=` hint (for
example `implementation="insert_conversation"`).

```python
# server/registry/users/content/cache/__init__.py
from . import mssql


def register(router: SubdomainRouter) -> None:
  router.add_function("list", version=1)
  router.add_function("get_gallery", version=1)
  ...
```

The derived provider map resolves to a provider-specific callable exported from
modules like `server/registry/users/content/cache/mssql.py`. Each implementation file
encodes the backend-specific queries and names its callables following the
`{operation}_v{version}` convention:

```python
# server/registry/users/content/cache/mssql.py
from server.registry.types import DBRequest, DBResponse


async def get_gallery_v1(request: DBRequest) -> DBResponse:
  ...
```

Each registration call binds the canonical `db:` key
(`db:users:content.cache:get_gallery:1`) to metadata about how to execute it. During
provider load the registry asserts that every registered key resolves to a
callable implementation. Startup fails fast if any bindings are missing so
module contracts cannot drift from provider coverage.

## 5. Provider maps and query stores
Providers live under `server/registry/providers`. For every supported database
engine we ship a module structured as follows:

```
server/registry/providers/
  __init__.py
  mssql.py
  postgres.py
  mysql.py
```

Each provider module exports a `PROVIDER_QUERIES` dictionary keyed by the same
`users.content.cache.list` identifiers referenced during registration. The
values are callables that receive `(request: DBRequest)` and return a
`DBResponse` (or awaitable `DBResponse` for async helpers). SQL strings and
stored procedure calls are defined here, keeping provider-specific details out
of the registry core.

When the registry initialises it loads the configured provider module and builds
an in-memory dispatch table:

```python
registry = RegistryRouter(default_provider="mssql")
registry.load_providers()
registry.register_domains()
```

The dispatch table maps a fully qualified `db:` key to a callable. The DbModule
only needs to hand over a `DBRequest`, and the registry will:

1. Resolve the domain/subdomain/function.
2. Fetch the matching provider callable from `PROVIDER_QUERIES`.
3. Execute it and wrap the result in a `DBResponse`.

## 6. Initialisation flow
1. **Application startup** instantiates `DbModule` and awaits `registry.startup()`.
2. **Registry startup** discovers all domain packages (importing each `register`
   function) and builds the routing tree.
3. Registry selects the provider map according to `DATABASE_PROVIDER` (mirroring
   the DbModule). The DbModule and registry share the provider name so that the
   correct provider queries are activated.
4. **DbModule.run** builds `DBRequest` and calls `registry.execute(request)`.
5. The registry performs the lookup and invokes the provider callable.
6. The provider executes the SQL, returning raw rows to be wrapped in a
   `DBResponse` and passed back up the stack.

## 7. Next steps
* Continue migrating legacy helpers into the consolidated namespaces such as
  `users.content.cache`, `users.content.files`, and `users.content.public`.
* Extract the existing MSSQL SQL from
  `server/modules/providers/database/mssql_provider/registry.py` into
  `server/registry/providers/mssql.py` under the new keys.
* Introduce placeholder `postgres.py` and `mysql.py` files that raise
  `NotImplementedError` for each function. This makes the required surface area
  explicit and ready for future engines.
* Update `DbModule` so that it constructs `DBRequest` objects and consumes
  `DBResponse`, renaming the current `DBResult` during the refactor to keep
  naming consistent across layers.
* Adjust modules (e.g. `StorageModule`) to import the new registry namespace
  once the refactor lands.

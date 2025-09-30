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
`server/registry` mirrors the `db:` namespace. The high-level packages we will
ship immediately are:

```
server/registry/
  accounts/
  content/
    cache/
      __init__.py
      mssql.py
      postgres.py
      mysql.py
    files/
      __init__.py
      mssql.py
      postgres.py
      mysql.py
    public/
      __init__.py
      mssql.py
      postgres.py
      mysql.py
  finance/
  public/
  system/
```

Storage-centric entries belong to the `content` domain because storage is one of
several content subsystems (others will include media processing, metadata,
content moderation, etc.). Mapping the existing URNs:

| Registry key | Target module | Notes |
| --- | --- | --- |
| `db:content:cache:list:1` | `content.cache` | User cache listing. |
| `db:content:cache:replace_user:1` | `content.cache` | Bulk refresh handler. |
| `db:content:cache:upsert:1` | `content.cache` | Upsert logic keeps helper `_get_storage_type_recid` locally. |
| `db:content:cache:delete:1` | `content.cache` | Delete single entry. |
| `db:content:cache:delete_folder:1` | `content.cache` | Delete folder subtree. |
| `db:content:cache:set_public:1` | `content.cache` | Toggle public flag. |
| `db:content:cache:set_reported:1` | `content.cache` | Toggle reported flag. |
| `db:content:cache:list_public:1` | `content.public` | Shared public listing helper. |
| `db:content:cache:list_reported:1` | `content.public` | Moderation list. |
| `db:content:cache:count_rows:1` | `content.cache` | Metrics helper. |
| `db:content:files:set_gallery:1` | `content.files` | Gallery state toggle. |
| `db:content:public:get_public_files:1` | `content.public` | Public gallery uses the same underlying SQL. |

During the migration the legacy `db:storage:*` keys will continue to exist behind
temporary aliases so that the DbModule can transition incrementally. Once the
modules are updated to call the new `db:content:*` operations the old names can
be dropped.

`content.public` exposes the shared public listing helpers that power
both the content module and the external public gallery without duplicating SQL
across domains.

## 4. Registry module contract
Each domain package will provide a `register(registry: RegistryRouter)` function
that registers its submodules. The implementation shape:

```python
# server/registry/content/__init__.py
from . import cache, files, public


def register(registry: RegistryRouter) -> None:
  domain = registry.domain("content")
  cache.register(domain.subdomain("cache"))
  files.register(domain.subdomain("files"))
  public.register(domain.subdomain("public"))
```

Each subdomain exposes a `register` helper that wires its functions to the
provider map. The leaf modules (`content/cache/__init__.py`,
`content/cache/mssql.py`, …) define their `db:` functions by pairing a
human-readable name with a provider target:

```python
# server/registry/content/cache/__init__.py
from . import mssql, postgres, mysql


def register(router: SubdomainRouter) -> None:
  router.add_function("list", version=1, provider_map="content.cache.list")
  router.add_function("get_gallery", version=1, provider_map="content.cache.get_gallery")
  ...
```

The `provider_map` string resolves to a provider-specific callable exported from
modules like `server/registry/content/cache/mssql.py`. Each implementation file
encodes the backend-specific queries:

```python
# server/registry/content/cache/mssql.py
from server.registry.types import DBRequest, DBResponse


async def get_gallery_v1(request: DBRequest) -> DBResponse:
  ...
```

Each registration call binds the canonical `db:` key
(`db:content:cache:get_gallery:1`) to metadata about how to execute it.

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
`content.cache.list` identifiers referenced during registration. The
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
* Create the scaffolding described above and migrate the storage functions into
  the `content.cache`, `content.files`, and `content.public` namespaces.
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

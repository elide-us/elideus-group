# Tests AGENT Instructions

This directory hosts the pytest suite for the backend and RPC layers.

---

## Structure & Conventions

- Tests are plain pytest modules; keep helper utilities inline or in
  `conftest.py` rather than creating new packages.
- Mirror the production layout: module-focused tests live next to their domain
  (e.g., `test_public_users_service.py`). Add new files following that naming
  pattern.
- Prefer `pytest.mark.asyncio` or `asyncio.run()` for coroutine helpers—stay
  consistent with surrounding tests.

---

## Fixture Guidance

- `tests/conftest.py` restores `rpc.helpers` between tests. If you monkeypatch
  global dispatcher tables (`HANDLERS`/`DISPATCHERS`), clean them up in a `try`
  / `finally` block.
- When stubbing modules, populate `app.state` with lightweight fakes that expose
  the same async API. Avoid importing heavy FastAPI modules unless required.

---

## When Adding Coverage

- Exercise the full request path: parse → service → module. Use fixtures to
  isolate external providers instead of calling real network or database code.
- Update **RPC.md** or other design docs when tests highlight new behavior.
- Keep assertions focused on security boundaries (roles, tokens) and serialized
  payload shapes so RPC generators stay accurate.

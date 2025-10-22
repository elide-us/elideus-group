"""Sanity checks for registry metadata and operation naming conventions."""

from __future__ import annotations

import importlib


def test_registered_ops_align_with_module_paths():
  registry = importlib.import_module("server.registry")
  providers = registry._registry_router._registry._providers
  assert providers, "registry should have providers registered"

  for provider, ops in providers.items():
    assert ops, f"provider {provider} must register operations"
    for op, spec in ops.items():
      domain, path, version = registry.parse_db_op(op)
      assert version > 0, f"{op} must use a positive version number"
      module_parts = spec.module.split(".")
      try:
        reg_index = module_parts.index("registry")
      except ValueError:  # pragma: no cover - defensive guard
        raise AssertionError(f"handler module missing registry segment: {spec.module}")
      package_parts = module_parts[reg_index + 1 : -1]
      assert package_parts, f"{op} must live under server.registry.*"
      assert domain == package_parts[0], f"{op} domain mismatch"
      expected_path = tuple(package_parts[1:])
      actual_path = tuple(path[:-1])
      assert actual_path == expected_path, f"{op} subdomain path mismatch"

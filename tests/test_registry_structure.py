"""Tests to ensure registry provider bindings match folder structure."""

from __future__ import annotations

from importlib import import_module

from server.registry import RegistryRouter


def test_registry_provider_structure() -> None:
  router = RegistryRouter()
  router.register_domains()

  format_errors: list[str] = []
  map_mismatches: list[str] = []
  missing_attrs: list[str] = []

  for binding in router.provider_bindings.values():
    parts = binding.canonical.split(":")
    if len(parts) != 5 or parts[0] != "db":
      format_errors.append(binding.canonical)
      continue

    _, domain, subdomain, function, _ = parts
    expected_map = f"{domain}.{subdomain}.{function}"
    if binding.provider_map != expected_map:
      map_mismatches.append(
        f"{binding.canonical}: provider_map='{binding.provider_map}', expected='{expected_map}'"
      )

    descriptor = binding.descriptor
    module_path = f"server.registry.{domain}.{subdomain}.mssql"
    attribute_name = f"{function}_v{binding.version}"
    if isinstance(descriptor, tuple) and len(descriptor) == 2:
      module_path, attribute_name = descriptor

    try:
      module = import_module(module_path)
    except ModuleNotFoundError as exc:
      missing_attrs.append(f"{binding.canonical}: missing module '{module_path}' ({exc})")
      continue

    if not hasattr(module, attribute_name):
      missing_attrs.append(
        f"{binding.canonical}: module '{module_path}' missing attribute '{attribute_name}'"
      )

  failures: list[str] = []
  if format_errors:
    joined = "\n  ".join(sorted(format_errors))
    failures.append("Invalid canonical bindings:\n  " + joined)
  if map_mismatches:
    joined = "\n  ".join(sorted(map_mismatches))
    failures.append("Provider map mismatches:\n  " + joined)
  if missing_attrs:
    joined = "\n  ".join(sorted(missing_attrs))
    failures.append("Missing provider implementations:\n  " + joined)

  if failures:
    formatted = "\n\n".join(failures)
    raise AssertionError("Registry structure mismatches detected:\n" + formatted)

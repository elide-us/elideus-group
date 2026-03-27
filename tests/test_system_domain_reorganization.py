"""Regression tests for system domain QR reorganization.

Validates subdomain consolidation, merges, removals, and cross-domain moves.
"""

import pytest


class TestSystemHandlerRegistration:
  """Verify the system domain handler has exactly the expected subdomains."""

  def test_expected_subdomains(self):
    from queryregistry.system.handler import HANDLERS
    expected = {
      "async_tasks", "batch_jobs", "config", "conversations",
      "personas", "public", "renewals", "roles", "workflows",
    }
    assert set(HANDLERS.keys()) == expected

  def test_removed_subdomains_absent(self):
    from queryregistry.system.handler import HANDLERS
    for name in ("public_vars", "configuration", "integrations",
                 "links", "routes", "models", "service_pages"):
      assert name not in HANDLERS, f"Removed subdomain '{name}' still in HANDLERS"


class TestPublicVarsAbsorbed:
  """Verify public_vars subdomain no longer exists and module uses config."""

  def test_public_vars_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.public_vars")

  def test_public_vars_module_uses_config(self):
    import inspect
    from server.modules.public_vars_module import PublicVarsModule
    import server.modules.public_vars_module as module
    source = inspect.getsource(module)
    assert "queryregistry.system.config" in source
    assert "queryregistry.system.public_vars" not in source


class TestPublicSubdomainMerge:
  """Verify links + routes merged into system.public."""

  def test_public_dispatchers(self):
    from queryregistry.system.public.handler import DISPATCHERS
    expected = {
      ("get_home_links", "1"),
      ("get_navbar_routes", "1"),
      ("get_routes", "1"),
      ("upsert_route", "1"),
      ("delete_route", "1"),
    }
    assert set(DISPATCHERS.keys()) == expected

  def test_request_builder_ops(self):
    from queryregistry.system.public import (
      get_home_links_request,
      get_navbar_routes_request,
      get_routes_request,
      upsert_route_request,
      delete_route_request,
    )
    from queryregistry.system.public.models import RoutePathParams, UpsertRouteParams

    assert get_home_links_request().op == "db:system:public:get_home_links:1"
    assert get_navbar_routes_request(1).op == "db:system:public:get_navbar_routes:1"
    assert get_routes_request().op == "db:system:public:get_routes:1"
    assert upsert_route_request(
      UpsertRouteParams(path="/test", name="Test", sequence=1, roles=0)
    ).op == "db:system:public:upsert_route:1"
    assert delete_route_request(
      RoutePathParams(path="/test")
    ).op == "db:system:public:delete_route:1"

  def test_links_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.links")

  def test_routes_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.routes")


class TestModelsRegistryMerged:
  """Verify models_registry merged into personas subdomain."""

  def test_persona_dispatchers_include_models(self):
    from queryregistry.system.personas.handler import DISPATCHERS
    model_keys = {
      ("models_list", "1"),
      ("models_get_by_name", "1"),
      ("models_upsert", "1"),
      ("models_delete", "1"),
    }
    assert model_keys.issubset(set(DISPATCHERS.keys()))

  def test_persona_dispatchers_include_originals(self):
    from queryregistry.system.personas.handler import DISPATCHERS
    persona_keys = {
      ("get_by_name", "1"),
      ("list", "1"),
      ("upsert", "1"),
      ("delete", "1"),
    }
    assert persona_keys.issubset(set(DISPATCHERS.keys()))

  def test_model_request_builders(self):
    from queryregistry.system.personas import (
      list_models_request,
      get_model_by_name_request,
      upsert_model_request,
      delete_model_request,
    )
    from queryregistry.system.personas.models import (
      ModelNameParams,
      UpsertModelParams,
      DeleteModelParams,
    )

    assert list_models_request().op == "db:system:personas:models_list:1"
    assert get_model_by_name_request(
      ModelNameParams(name="gpt-4o")
    ).op == "db:system:personas:models_get_by_name:1"
    assert upsert_model_request(
      UpsertModelParams(name="gpt-4o")
    ).op == "db:system:personas:models_upsert:1"
    assert delete_model_request(
      DeleteModelParams(name="gpt-4o")
    ).op == "db:system:personas:models_delete:1"

  def test_models_registry_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.models_registry")

  def test_model_types_importable_from_personas(self):
    from queryregistry.system.personas.models import (
      ModelNameParams,
      UpsertModelParams,
      DeleteModelParams,
      ModelRecord,
    )
    assert ModelNameParams is not None
    assert UpsertModelParams is not None
    assert DeleteModelParams is not None
    assert ModelRecord is not None


class TestServicePagesMovedToContent:
  """Verify service_pages moved from system to content.pages."""

  def test_content_pages_registered(self):
    from queryregistry.content.handler import HANDLERS
    assert "pages" in HANDLERS

  def test_system_service_pages_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.service_pages")




class TestWorkflowsSubdomain:
  """Verify workflows subdomain registration and request builder ops."""

  def test_workflow_dispatchers(self):
    from queryregistry.system.workflows.handler import DISPATCHERS
    expected = {
      ("get_active_workflow", "1"),
      ("list_workflow_steps", "1"),
      ("create_workflow_run", "1"),
      ("get_workflow_run", "1"),
      ("list_workflow_runs", "1"),
      ("update_workflow_run", "1"),
      ("create_workflow_run_step", "1"),
      ("update_workflow_run_step", "1"),
      ("list_workflow_run_steps", "1"),
    }
    assert set(DISPATCHERS.keys()) == expected

  def test_workflow_request_builders(self):
    from queryregistry.system.workflows import get_active_workflow_request
    from queryregistry.system.workflows.models import GetActiveWorkflowParams

    req = get_active_workflow_request(GetActiveWorkflowParams(name="conversation.persona"))
    assert req.op == "db:system:workflows:get_active_workflow:1"


class TestConfigurationRemoved:
  """Verify configuration stub deleted."""

  def test_configuration_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.configuration")


class TestIntegrationsRemoved:
  """Verify integrations stub deleted."""

  def test_integrations_package_removed(self):
    import importlib
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.system.integrations")


class TestNoLegacyOpStrings:
  """Verify no request builders produce legacy op formats."""

  def test_no_public_vars_ops(self):
    from queryregistry.system.config import get_config_request
    from queryregistry.system.config.models import ConfigKeyParams
    req = get_config_request(ConfigKeyParams(key="version"))
    assert "public_vars" not in req.op

  def test_no_links_ops(self):
    from queryregistry.system.public import get_home_links_request
    assert ":links:" not in get_home_links_request().op

  def test_no_routes_ops(self):
    from queryregistry.system.public import get_routes_request
    assert ":routes:" not in get_routes_request().op

  def test_no_models_registry_ops(self):
    from queryregistry.system.personas import list_models_request
    req = list_models_request()
    assert "models_registry" not in req.op
    assert req.op.startswith("db:system:personas:")

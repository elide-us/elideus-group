import pathlib
import sys
import types

import pytest
from pydantic import ValidationError

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)


def test_service_pages_dispatchers_registered():
  from rpc.service.pages import DISPATCHERS

  assert set(DISPATCHERS.keys()) == {
    ("list", "1"),
    ("create", "1"),
    ("update", "1"),
    ("delete", "1"),
  }


def test_service_pages_handler_registered_in_service_handlers():
  from rpc.service import HANDLERS
  from rpc.service.pages.handler import handle_pages_request

  assert "pages" in HANDLERS
  assert HANDLERS["pages"] is handle_pages_request


def test_service_pages_create_page_model_validates_required_fields():
  from rpc.service.pages.models import ServicePagesCreatePage1

  payload = ServicePagesCreatePage1(
    slug="privacy-policy",
    title="Privacy Policy",
    content="# Privacy Policy",
  )

  assert payload.slug == "privacy-policy"
  assert payload.title == "Privacy Policy"
  assert payload.content == "# Privacy Policy"

  with pytest.raises(ValidationError):
    ServicePagesCreatePage1(title="Missing slug", content="body")

  with pytest.raises(ValidationError):
    ServicePagesCreatePage1(slug="missing-title", content="body")

  with pytest.raises(ValidationError):
    ServicePagesCreatePage1(slug="missing-content", title="Missing content")


def test_service_pages_update_page_model_validates_required_fields():
  from rpc.service.pages.models import ServicePagesUpdatePage1

  payload = ServicePagesUpdatePage1(recid=1001, title="Updated")

  assert payload.recid == 1001
  assert payload.title == "Updated"

  with pytest.raises(ValidationError):
    ServicePagesUpdatePage1(title="Missing recid")


def test_service_pages_delete_page_model_validates_required_fields():
  from rpc.service.pages.models import ServicePagesDeletePage1

  payload = ServicePagesDeletePage1(recid=1001)

  assert payload.recid == 1001

  with pytest.raises(ValidationError):
    ServicePagesDeletePage1()

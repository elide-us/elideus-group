import pathlib
import sys
import types

import pytest
from pydantic import ValidationError

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)


def test_users_pages_dispatchers_registered():
  from rpc.users.pages import DISPATCHERS

  assert set(DISPATCHERS.keys()) == {
    ("create_version", "1"),
    ("list_versions", "1"),
    ("get_version", "1"),
  }


def test_users_pages_handler_registered_in_users_handlers():
  from rpc.users import HANDLERS
  from rpc.users.pages.handler import handle_pages_request

  assert HANDLERS["pages"] is handle_pages_request


def test_users_pages_create_version_model_validates_required_fields():
  from rpc.users.pages.models import UsersPagesCreateVersion1

  payload = UsersPagesCreateVersion1(slug="hello-world", content="# Heading", summary="revision")

  assert payload.slug == "hello-world"
  assert payload.content == "# Heading"
  assert payload.summary == "revision"

  with pytest.raises(ValidationError):
    UsersPagesCreateVersion1(content="# Heading")


def test_users_pages_list_versions_model_validates_required_fields():
  from rpc.users.pages.models import UsersPagesListVersions1

  payload = UsersPagesListVersions1(slug="hello-world")

  assert payload.slug == "hello-world"

  with pytest.raises(ValidationError):
    UsersPagesListVersions1()


def test_users_pages_get_version_model_validates_required_fields():
  from rpc.users.pages.models import UsersPagesGetVersion1

  payload = UsersPagesGetVersion1(slug="hello-world", version=3)

  assert payload.slug == "hello-world"
  assert payload.version == 3

  with pytest.raises(ValidationError):
    UsersPagesGetVersion1(slug="hello-world")

"""System service page registry helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from .model import (
  CreateServicePageParams,
  DeleteServicePageParams,
  GetServicePageByRouteParams,
  GetServicePageParams,
  ListServicePagesParams,
  ServicePageRecord,
  UpdateServicePageParams,
)

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "create_service_page_request",
  "delete_service_page_request",
  "get_service_page_by_route_request",
  "get_service_page_request",
  "list_service_pages_request",
  "register",
  "update_service_page_request",
  "CreateServicePageParams",
  "DeleteServicePageParams",
  "GetServicePageByRouteParams",
  "GetServicePageParams",
  "ListServicePagesParams",
  "ServicePageRecord",
  "UpdateServicePageParams",
]

_OP_PREFIX = "db:system:service_pages"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_service_pages_request(*, include_inactive: bool = True) -> DBRequest:
  params: ListServicePagesParams = {}
  if not include_inactive:
    params["element_is_active"] = True
  return DBRequest(op=_op("list"), params=params)


def get_service_page_request(*, recid: int) -> DBRequest:
  params: GetServicePageParams = {"recid": recid}
  return DBRequest(op=_op("get"), params=params)


def get_service_page_by_route_request(
  *,
  route_name: str,
  active_only: bool = True,
) -> DBRequest:
  params: GetServicePageByRouteParams = {"element_route_name": route_name}
  if active_only:
    params["element_is_active"] = True
  return DBRequest(op=_op("get_by_route"), params=params)


def create_service_page_request(
  *,
  recid: int,
  route_name: str,
  page_blob: str,
  created_by: str,
  modified_by: str,
  version: int | None = None,
  is_active: bool | None = None,
) -> DBRequest:
  params: CreateServicePageParams = {
    "recid": recid,
    "element_route_name": route_name,
    "element_pageblob": page_blob,
    "element_created_by": created_by,
    "element_modified_by": modified_by,
  }
  if version is not None:
    params["element_version"] = version
  if is_active is not None:
    params["element_is_active"] = is_active
  return DBRequest(op=_op("create"), params=params)


def update_service_page_request(
  *,
  recid: int,
  modified_by: str,
  route_name: str | None = None,
  page_blob: str | None = None,
  version: int | None = None,
  is_active: bool | None = None,
) -> DBRequest:
  params: UpdateServicePageParams = {
    "recid": recid,
    "element_modified_by": modified_by,
  }
  if route_name is not None:
    params["element_route_name"] = route_name
  if page_blob is not None:
    params["element_pageblob"] = page_blob
  if version is not None:
    params["element_version"] = version
  if is_active is not None:
    params["element_is_active"] = is_active
  return DBRequest(op=_op("update"), params=params)


def delete_service_page_request(*, recid: int) -> DBRequest:
  params: DeleteServicePageParams = {"recid": recid}
  return DBRequest(op=_op("delete"), params=params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("list", version=1)
  router.add_function("get", version=1)
  router.add_function("get_by_route", version=1)
  router.add_function("create", version=1)
  router.add_function("update", version=1)
  router.add_function("delete", version=1)

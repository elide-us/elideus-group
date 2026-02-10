"""Typed contracts for service page registry operations."""

from __future__ import annotations

from typing import NotRequired, TypedDict

__all__ = [
  "CreateServicePageParams",
  "DeleteServicePageParams",
  "GetServicePageByRouteParams",
  "GetServicePageParams",
  "ListServicePagesParams",
  "ServicePageRecord",
  "UpdateServicePageParams",
]


class ServicePageRecord(TypedDict, total=False):
  recid: int
  element_route_name: str
  element_pageblob: str
  element_version: int
  element_created_on: str
  element_modified_on: str
  element_created_by: str
  element_modified_by: str
  element_is_active: bool


class ListServicePagesParams(TypedDict, total=False):
  element_is_active: NotRequired[bool]


class GetServicePageParams(TypedDict):
  recid: int


class GetServicePageByRouteParams(TypedDict):
  element_route_name: str
  element_is_active: NotRequired[bool]


class CreateServicePageParams(TypedDict):
  recid: int
  element_route_name: str
  element_pageblob: str
  element_created_by: str
  element_modified_by: str
  element_version: NotRequired[int]
  element_is_active: NotRequired[bool]


class UpdateServicePageParams(TypedDict):
  recid: int
  element_modified_by: str
  element_route_name: NotRequired[str]
  element_pageblob: NotRequired[str]
  element_version: NotRequired[int]
  element_is_active: NotRequired[bool]


class DeleteServicePageParams(TypedDict):
  recid: int

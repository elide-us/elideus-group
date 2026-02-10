"""Data models for the QueryRegistry namespace.

These local models are canonical for QueryRegistry and should be preferred
over legacy registry types to prevent mixed imports.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, Mapping, Sequence

__all__ = ["DBRequest", "DBResponse"]


class DBRequest:
  """Representation of a query registry request (canonical QueryRegistry type)."""

  __slots__ = ("op", "payload")

  def __init__(
    self,
    *,
    op: str,
    payload: Mapping[str, Any],
  ) -> None:
    if not op:
      raise ValueError("op is required for DBRequest")
    self.op = op
    self.payload: Dict[str, Any] = dict(payload)

  def copy(self) -> "DBRequest":
    return DBRequest(op=self.op, payload=dict(self.payload))

  def with_payload(self, data: Mapping[str, Any]) -> "DBRequest":
    new = self.copy()
    new.payload.update(data)
    return new


class DBResponse:
  """Representation of a query registry response (canonical QueryRegistry type)."""

  __slots__ = ("op", "payload", "rowcount")

  def __init__(
    self,
    *,
    op: str = "",
    payload: Any | None = None,
    rows: Sequence[Mapping[str, Any]] | None = None,
    rowcount: int | None = None,
  ) -> None:
    if rows is not None:
      payload = [dict(row) for row in rows]
      if rowcount is None:
        rowcount = len(payload)
    self.op = op
    if payload is None:
      payload = []
    self.payload = payload
    if rowcount is None:
      rowcount = 0
    self.rowcount = rowcount

  @property
  def rows(self) -> list[Mapping[str, Any]]:
    data = self.payload
    if data is None:
      return []
    if isinstance(data, list):
      return data
    if isinstance(data, (tuple, set)):
      return [dict(item) if isinstance(item, Mapping) else item for item in data]
    if isinstance(data, Mapping):
      return [data]
    return [data]

  def attach_op(self, op: str) -> "DBResponse":
    self.op = op
    return self

  def model_dump(self) -> dict[str, Any]:
    return {
      "op": self.op,
      "payload": self.payload,
      "rowcount": self.rowcount,
      "rows": self.rows,
    }

  def __iter__(self) -> Iterator[tuple[str, Any]]:  # type: ignore[override]
    yield from {"rows": self.rows, "rowcount": self.rowcount}.items()

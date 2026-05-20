from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

APPROVED_PATH_PREFIXES = (
  "server/modules/providers/",
)

EXCLUDED_PATH_PREFIXES = (
  ".git/",
  ".venv/",
  "node_modules/",
  "client/",
)


def _is_excluded(path: Path) -> bool:
  rel = path.relative_to(ROOT).as_posix()
  return any(rel.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)


def _is_allowlisted(path: Path) -> bool:
  rel = path.relative_to(ROOT).as_posix()
  return any(rel.startswith(prefix) for prefix in APPROVED_PATH_PREFIXES)


def _find_direct_db_run_calls(path: Path) -> list[int]:
  source = path.read_text(encoding="utf-8")
  tree = ast.parse(source, filename=str(path))

  lines: list[int] = []
  for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
      continue
    func = node.func
    if not isinstance(func, ast.Attribute):
      continue
    if func.attr != "run":
      continue
    if not isinstance(func.value, ast.Name):
      continue
    if func.value.id != "db":
      continue
    lines.append(node.lineno)

  return sorted(lines)


def main() -> int:
  offenders: list[tuple[str, int]] = []

  for path in ROOT.rglob("*.py"):
    if _is_excluded(path) or _is_allowlisted(path):
      continue

    for line_no in _find_direct_db_run_calls(path):
      offenders.append((path.relative_to(ROOT).as_posix(), line_no))

  if offenders:
    print("Direct db.run(...) usage is restricted to approved infrastructure paths only.")
    print("Move business/module data access to canonical QueryRegistry request builders/operations.")
    print("\nOffending call sites:")
    for rel_path, line_no in offenders:
      print(f"  - {rel_path}:{line_no}")
    return 1

  print("db.run boundary check passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

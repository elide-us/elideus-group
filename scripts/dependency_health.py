#!/usr/bin/env python3
"""Interactive dependency inspection utility for selective package maintenance."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
PACKAGE_JSON_PATH = FRONTEND_DIR / "package.json"
PYTHON_REQUIREMENT_PATHS = [
  REPO_ROOT / "requirements.txt",
  REPO_ROOT / "requirements-dev.txt",
]

NODE_GROUPS: Dict[str, Dict[str, Iterable[str]]] = {
  "mui": {
    "label": "MUI and Emotion styling",
    "packages": [
      "@mui/material",
      "@mui/icons-material",
      "@emotion/react",
      "@emotion/styled",
    ],
  },
  "atproto": {
    "label": "ATProto client SDK",
    "packages": [
      "@atproto/api",
      "@atproto/crypto",
      "@atproto/identity",
      "@atproto/lexicon",
      "@atproto/xrpc",
    ],
  },
  "react": {
    "label": "React core runtime",
    "packages": [
      "react",
      "react-dom",
      "react-router-dom",
    ],
  },
}

PYTHON_GROUPS: Dict[str, Dict[str, Iterable[str]]] = {
  "atproto": {
    "label": "ATProto Python client",
    "packages": ["atproto"],
  },
  "fastapi-stack": {
    "label": "FastAPI runtime trio",
    "packages": ["fastapi", "uvicorn", "gunicorn"],
  },
  "async-io": {
    "label": "Async IO helpers",
    "packages": ["aiohttp", "aiofiles", "aioodbc", "asyncpg"],
  },
}


def read_package_json() -> Dict[str, Dict[str, str]]:
  if not PACKAGE_JSON_PATH.exists():
    raise FileNotFoundError(f"Missing package.json at {PACKAGE_JSON_PATH}")
  with PACKAGE_JSON_PATH.open("r", encoding="utf-8") as handle:
    return json.load(handle)


def read_python_requirements() -> Dict[str, List[str]]:
  results: Dict[str, List[str]] = {}
  for path in PYTHON_REQUIREMENT_PATHS:
    if not path.exists():
      continue
    name = path.name
    packages: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
      for raw_line in handle:
        line = raw_line.strip()
        if not line or line.startswith("#"):
          continue
        packages.append(line)
    results[name] = packages
  return results


def run_command(command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    cwd=str(cwd) if cwd else None,
    capture_output=True,
    text=True,
    check=False,
  )


def load_pip_outdated(python_executable: str) -> Dict[str, Dict[str, str]]:
  command = [python_executable, "-m", "pip", "list", "--outdated", "--format", "json"]
  result = run_command(command, cwd=REPO_ROOT)
  if result.returncode != 0:
    raise RuntimeError(
      f"pip outdated command failed with code {result.returncode}: {result.stderr.strip()}"
    )
  try:
    data = json.loads(result.stdout)
  except json.JSONDecodeError as error:
    raise RuntimeError("Unable to parse pip outdated output") from error
  return {entry["name"].lower(): entry for entry in data}


def load_npm_outdated(npm_executable: str) -> Dict[str, Dict[str, str]]:
  command = [npm_executable, "outdated", "--json"]
  result = run_command(command, cwd=FRONTEND_DIR)
  if result.returncode not in (0, 1):
    raise RuntimeError(
      f"npm outdated command failed with code {result.returncode}: {result.stderr.strip()}"
    )
  if not result.stdout.strip():
    return {}
  try:
    data = json.loads(result.stdout)
  except json.JSONDecodeError as error:
    raise RuntimeError("Unable to parse npm outdated output") from error
  return {name.lower(): values for name, values in data.items()}


def print_python_summary(requirements: Dict[str, List[str]]) -> None:
  print("\nPython requirement files:")
  for name, packages in requirements.items():
    print(f"  {name} ({len(packages)} entries)")
    for package in packages:
      print(f"    - {package}")


def print_node_summary(package_json: Dict[str, Dict[str, str]]) -> None:
  print("\nNode dependency overview:")
  for section in ("dependencies", "devDependencies"):
    entries = package_json.get(section, {})
    print(f"  {section} ({len(entries)} entries)")
    for name, version in entries.items():
      print(f"    - {name}: {version}")


def print_group_status(
  label: str,
  group_packages: Iterable[str],
  outdated_index: Dict[str, Dict[str, str]],
  note: str,
) -> None:
  print(f"\n[{label}] {note}")
  for package in group_packages:
    entry = outdated_index.get(package.lower())
    if not entry:
      print(f"  ✓ {package} is up to date or pinned manually")
      continue
    latest = entry.get("latest") or entry.get("latestVersion")
    current = entry.get("current") or entry.get("installed")
    wanted = entry.get("wanted") or entry.get("latest")
    print(f"  • {package} → current: {current}, wanted: {wanted}, latest: {latest}")


def inspect_groups(
  node_outdated: Dict[str, Dict[str, str]],
  python_outdated: Dict[str, Dict[str, str]],
) -> None:
  print("\nTargeted group status:")
  for key, config in NODE_GROUPS.items():
    print_group_status(
      label=f"Node :: {config['label']} ({key})",
      group_packages=config["packages"],
      outdated_index=node_outdated,
      note="Run npm install within frontend/ to update as a bundle.",
    )
  for key, config in PYTHON_GROUPS.items():
    print_group_status(
      label=f"Python :: {config['label']} ({key})",
      group_packages=config["packages"],
      outdated_index=python_outdated,
      note="Use py -m pip install --upgrade while in a virtual environment.",
    )


def determine_python_default() -> str:
  if os.name == "nt":
    return "py"
  return sys.executable


def run_interactive(python_executable: str, npm_executable: str) -> None:
  requirements = read_python_requirements()
  package_json = read_package_json()
  node_outdated: Dict[str, Dict[str, str]] = {}
  python_outdated: Dict[str, Dict[str, str]] = {}
  options = {
    "1": "Show Python requirement entries",
    "2": "Show Node dependency entries",
    "3": "Refresh pip outdated report",
    "4": "Refresh npm outdated report",
    "5": "Review targeted package groups",
    "6": "Quit",
  }
  while True:
    print("\nDependency maintenance menu:")
    for key, label in options.items():
      print(f"  {key}. {label}")
    choice = input("Select an option: ").strip()
    if choice == "1":
      print_python_summary(requirements)
    elif choice == "2":
      print_node_summary(package_json)
    elif choice == "3":
      try:
        python_outdated = load_pip_outdated(python_executable)
        print("\nUpdated pip outdated cache.")
      except Exception as error:
        print(f"\nUnable to refresh pip data: {error}")
    elif choice == "4":
      try:
        node_outdated = load_npm_outdated(npm_executable)
        print("\nUpdated npm outdated cache.")
      except Exception as error:
        print(f"\nUnable to refresh npm data: {error}")
    elif choice == "5":
      inspect_groups(node_outdated, python_outdated)
    elif choice == "6":
      print("Exiting.")
      return
    else:
      print("Unknown option. Please choose a valid number.")


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--python",
    dest="python_executable",
    default=determine_python_default(),
    help="Python launcher to use for pip commands (default: %(default)s)",
  )
  parser.add_argument(
    "--npm",
    dest="npm_executable",
    default="npm",
    help="npm executable to use (default: %(default)s)",
  )
  parser.add_argument(
    "--non-interactive",
    action="store_true",
    help="Print summaries and exit without menu prompts.",
  )
  parser.add_argument(
    "--skip-outdated",
    action="store_true",
    help="Do not execute pip/npm outdated checks in non-interactive mode.",
  )
  args = parser.parse_args()
  requirements = read_python_requirements()
  package_json = read_package_json()
  if args.non_interactive:
    print_python_summary(requirements)
    print_node_summary(package_json)
    python_outdated: Dict[str, Dict[str, str]] = {}
    node_outdated: Dict[str, Dict[str, str]] = {}
    if args.skip_outdated:
      print("\nSkipping pip and npm outdated checks by request.")
    else:
      try:
        python_outdated = load_pip_outdated(args.python_executable)
      except Exception as error:
        print(f"\nUnable to refresh pip data: {error}")
      try:
        node_outdated = load_npm_outdated(args.npm_executable)
      except Exception as error:
        print(f"\nUnable to refresh npm data: {error}")
    inspect_groups(node_outdated, python_outdated)
    return
  run_interactive(args.python_executable, args.npm_executable)


if __name__ == "__main__":
  main()

"""Entry point for the database management CLI."""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
  sys.path.insert(0, REPO_ROOT)

from server.modules.database_cli.cli import run_repl

if __name__ == "__main__":
  run_repl()

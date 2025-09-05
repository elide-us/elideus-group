from __future__ import annotations

"""Run both RPC generation steps for library models and client functions."""

from generate_rpc_library import main as gen_library
from generate_rpc_client import main as gen_client


def main() -> None:
  gen_library()
  gen_client()


if __name__ == '__main__':
  main()

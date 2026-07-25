"""Extract inline [[8HEX]] wiki-links from entry bodies into real graph edges.

Implements FDD-ORACLE-MEM-UNIFY-01 §4 B1 (step 4 of §7).

The memory bank carries two parallel edge representations: inline [[8HEX]]
citations in pub_body, and rows in agent_memory_references. They are not the
same graph, and the prose one is authoritative — D9FE6CE0 has 5 inline
citations against 1 reference row, 60CCA038 has 5 against 2. The consequences
are that pub_ref_count reads 0 on most recent nodes (so authority collapses to
a near-flat ordering), and traversal cannot follow a link without downloading
and regexing a full body.

This script promotes the prose graph into the edge table so the edge layer is
the graph.

RESOLUTION IS GLOBAL. An 8-hex prefix is matched against every entry in the
bank regardless of project, because the citations cross projects — several
elideus-group bodies cite 'general' rules such as 4F7A5B2D. Filtering by
project would silently drop those and report them as dangling.

Everything extracted is written as pub_ref_kind='cites' with weight 1.0. Prose
does not reliably signal edge semantics, so 'cites' is the honest floor; the
existing UQ(ref_from_guid, ref_to_guid, pub_ref_kind) makes the load idempotent
and will not overwrite the hand-authored edges that already carry better kinds.

Nothing is guessed. A prefix matching zero entries is reported as a dangling
citation; a prefix matching more than one is reported as ambiguous and skipped.
Self-edges are skipped. pub_body is read but never modified — the inline links
stay in the prose, because removing them is a body rewrite and this migration
does not touch bodies.

Usage:
    python scripts/extract_memory_wikilinks.py           # dry run + reports
    python scripts/extract_memory_wikilinks.py --apply   # insert the edges
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT

load_dotenv(os.path.join(REPO_ROOT, ".env"))

WIKILINK_RE = re.compile(r"\[\[([0-9A-Fa-f]{8})\]\]")


def connect() -> pyodbc.Connection:
  """Connect to the test database only — never fall back to production.

  See the matching note in scripts/load_memory_documents.py. This script writes
  edges into the memory graph; an accidental production connection would be
  materially worse than a failed run.
  """
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV")
  if not dsn:
    raise RuntimeError(
      "Missing AZURE_SQL_CONNECTION_STRING_DEV (the elideus-group-test database). "
      "This script will not fall back to AZURE_SQL_CONNECTION_STRING — that is production."
    )
  # autocommit=True is required — see the note in load_memory_documents.py.
  # autocommit=False nests the explicit BEGIN, so COMMIT never durably commits
  # and close() silently rolls back an apparently successful run.
  return pyodbc.connect(dsn, autocommit=True)


def extract(apply: bool) -> None:
  conn = connect()
  cursor = conn.cursor()
  try:
    rows = cursor.execute(
      "SELECT key_guid, pub_project, pub_title, pub_body FROM dbo.agent_memory_entries"
    ).fetchall()
    print(f"entries scanned      : {len(rows)}")

    # Prefix -> [guid]. Global by design; see the module docstring.
    prefixes: dict[str, list[str]] = collections.defaultdict(list)
    for key_guid, _project, _title, _body in rows:
      prefixes[str(key_guid)[:8].upper()].append(str(key_guid).upper())

    ambiguous_prefixes = {p: g for p, g in prefixes.items() if len(g) > 1}

    pairs: set[tuple[str, str]] = set()
    dangling: collections.Counter = collections.Counter()
    dangling_hosts: dict[str, set[str]] = collections.defaultdict(set)
    ambiguous_hits: collections.Counter = collections.Counter()
    self_edges = 0
    occurrences = 0
    hosts = 0

    for key_guid, project, title, body in rows:
      src = str(key_guid).upper()
      found = WIKILINK_RE.findall(f"{title or ''}\n{body or ''}")
      if found:
        hosts += 1
      occurrences += len(found)
      for raw in found:
        prefix = raw.upper()
        targets = prefixes.get(prefix)
        if not targets:
          dangling[prefix] += 1
          dangling_hosts[prefix].add(f"{str(key_guid)[:8]}({project})")
          continue
        if len(targets) > 1:
          ambiguous_hits[prefix] += 1
          continue
        dst = targets[0]
        if dst == src:
          self_edges += 1
          continue
        pairs.add((src, dst))

    print(f"entries with links   : {hosts}")
    print(f"[[8HEX]] occurrences : {occurrences}")
    print(f"distinct edges       : {len(pairs)}")
    print(f"self-edges skipped   : {self_edges}")
    print(f"dangling citations   : {sum(dangling.values())} ({len(dangling)} distinct prefixes)")
    print(f"ambiguous citations  : {sum(ambiguous_hits.values())} ({len(ambiguous_hits)} distinct prefixes)")

    if dangling:
      print("\n-- DANGLING (prefix resolves to no entry; nothing inserted) --")
      for prefix, n in dangling.most_common():
        cited_by = ", ".join(sorted(dangling_hosts[prefix])[:5])
        print(f"   [[{prefix}]]  x{n}  cited by {cited_by}")

    if ambiguous_hits:
      print("\n-- AMBIGUOUS (prefix resolves to >1 entry; SKIPPED, resolve by hand) --")
      for prefix, n in ambiguous_hits.most_common():
        print(f"   [[{prefix}]]  x{n}  ->  {', '.join(ambiguous_prefixes[prefix])}")

    if not apply:
      print("\nDRY RUN — no edges written. Re-run with --apply.")
      return

    # Batch-prepare into a temp table, then flush as one set-based insert so the
    # existing UQ(from,to,kind) decides what is genuinely new.
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute("CREATE TABLE #wikilink_edges (ref_from_guid UNIQUEIDENTIFIER, ref_to_guid UNIQUEIDENTIFIER);")
    cursor.fast_executemany = True
    cursor.executemany("INSERT INTO #wikilink_edges (ref_from_guid, ref_to_guid) VALUES (?, ?);", sorted(pairs))

    cursor.execute(
      """
      INSERT INTO dbo.agent_memory_references (ref_from_guid, ref_to_guid, pub_ref_kind, pub_weight, pub_is_active)
      SELECT t.ref_from_guid, t.ref_to_guid, N'cites', 1.0, 1
        FROM #wikilink_edges t
       WHERE NOT EXISTS (
             SELECT 1 FROM dbo.agent_memory_references r
              WHERE r.ref_from_guid = t.ref_from_guid
                AND r.ref_to_guid   = t.ref_to_guid
                AND r.pub_ref_kind  = N'cites');
      """
    )
    inserted = cursor.rowcount
    cursor.execute("DROP TABLE #wikilink_edges;")
    cursor.execute("COMMIT TRANSACTION;")

    total = cursor.execute("SELECT COUNT(*) FROM dbo.agent_memory_references WHERE pub_is_active = 1").fetchone()[0]
    print(f"\nedges inserted       : {inserted}  ({len(pairs) - inserted} already existed)")
    print(f"active edges in bank : {total}")
    print("\nNext: run migrations/v0.13.8.1_memory_unify_data.sql (B2-B6).")
  except Exception:
    try:
      cursor.execute("ROLLBACK TRANSACTION;")
    except Exception:
      pass
    raise
  finally:
    conn.close()


def main() -> None:
  parser = argparse.ArgumentParser(description="Promote inline [[8HEX]] wiki-links into agent_memory_references")
  parser.add_argument("--apply", action="store_true", help="Write the edges (default is a dry run)")
  args = parser.parse_args()
  extract(apply=args.apply)


if __name__ == "__main__":
  main()

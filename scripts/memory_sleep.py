"""The memory sleep cycle — FDD-ORACLE-MEM-UNIFY-01 Part D.

Runs the maintenance pass over the memory graph: mechanical repairs applied
directly (D1), judgment-requiring changes PROPOSED into
agent_memory_maintenance_queue and never executed (D2), and a morning report
rendered from what happened (D4).

RELATIONSHIP TO THE AUTOMATION MODULE
  FDD §6 assumed "the existing production scheduler infrastructure — same
  pattern as StorageModule._reindex_loop". That runner does not exist on this
  branch. The automation SCHEMA does: system_workflows / _workflow_actions /
  _workflow_runs / _run_actions / _scheduled_tasks, the db:system:workflows:*
  ops, and a full spec at pagespec/system/SystemAutomationPages.md (recoverable
  from tag mem-unify-01/pre-doc-deletion).

  This script holds the sleep-cycle LOGIC and is directly runnable. It is not a
  substitute for the automation module — that is being rebuilt separately, and
  when it lands the logic here becomes the body of the RPC function a workflow
  action dispatches to. Note system_workflow_actions.functions_recid is a
  NOT NULL FK to reflection_rpc_functions, so an action must resolve to a
  registered RPC function; a workflow cannot call a bare module method.

  Keeping the logic in one place and calling it from two entry points is not
  duplication. Duplication would be a second implementation of the maintenance
  pass living inside the automation module.

THE STRIPPER IS NOT IMPLEMENTED, DELIBERATELY
  §D3 allows a stripper that may DELETE but never REWRITE, validating that
  retained text is a literal subsequence of the source. That constraint is
  correct and the operation is still the single most dangerous thing in the
  FDD — it edits bodies. It is proposed here (op='strip') and left for a human
  to apply. Nothing in this script writes pub_body.

  agent_memory_documents is never touched at all: no SELECT for modification,
  no UPDATE, no DELETE. The verbatim store exists because compression destroyed
  these documents once already.

Usage:
    python scripts/memory_sleep.py                 # dry run — report only
    python scripts/memory_sleep.py --apply         # apply D1, enqueue D2
    python scripts/memory_sleep.py --apply --quiet # for cron
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections import defaultdict

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT
from server.helpers import memory_sleep_ops as ops

load_dotenv(os.path.join(REPO_ROOT, ".env"))

BODY_CAP = ops.BODY_CAP
_WS_RE = re.compile(r"\s+")


def connect() -> pyodbc.Connection:
  """Test database only — never fall back to production. See load_memory_documents.py.

  autocommit=True is required: with autocommit=False an explicit BEGIN nests,
  COMMIT never durably commits, and close() rolls back a run that reported
  success (memory entry 580F2874).
  """
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV")
  if not dsn:
    raise RuntimeError(
      "Missing AZURE_SQL_CONNECTION_STRING_DEV (elideus-group-test). This script "
      "will not fall back to AZURE_SQL_CONNECTION_STRING — that is production."
    )
  return pyodbc.connect(dsn, autocommit=True)


_GIT_HISTORY_CACHE: dict[str, bool] = {}


def _has_git_history(pub_source: str) -> bool:
  """True if pub_source names a path that ever existed in THIS repo's history.

  pub_source is free text — sometimes a clean path ('pagespec/cms/ObjectTree.md'),
  sometimes prose naming several ('BUILD.md + AGENTS.md'), sometimes a label for
  a document that never existed ('docs/auth.md' for a unity design authored in
  MCP only). Extract every path-shaped token and ask git about each; one hit is
  enough to make the proposal actionable.
  """
  hits = re.findall(r"[\w./-]+\.md", pub_source or "")
  for path in hits:
    if path in _GIT_HISTORY_CACHE:
      if _GIT_HISTORY_CACHE[path]:
        return True
      continue
    try:
      out = subprocess.check_output(
        ["git", "log", "--all", "--oneline", "-1", "--", path],
        cwd=REPO_ROOT, stderr=subprocess.DEVNULL,
      ).decode().strip()
    except subprocess.CalledProcessError:
      out = ""
    _GIT_HISTORY_CACHE[path] = bool(out)
    if out:
      return True
  return False


def normalised_hash(body: str) -> str:
  """Hash for exact-duplicate detection: whitespace-collapsed, case-folded.

  Deliberately NOT fuzzy. A near-miss is a judgment call and belongs in the
  queue as a merge proposal for a human, not in an automatic pass.
  """
  return hashlib.sha256(_WS_RE.sub(" ", body or "").strip().casefold().encode("utf-8")).hexdigest()


# ── D1: automatic operations (mechanical, reversible, no judgment) ───────────

def d1_recompute_counts(cur, apply: bool) -> dict:
  drift = cur.execute(ops.D1_REFCOUNT_DRIFT).fetchone()[0]
  if apply and drift:
    cur.execute(ops.D1_REFCOUNT_REPAIR)
  return {"op": "recompute_ref_count", "drifted": drift, "applied": bool(apply and drift)}


def d1_flag_legacy(cur, apply: bool) -> dict:
  n = cur.execute(
    ops.D1_LEGACY_COUNT, [BODY_CAP]
  ).fetchone()[0]
  if apply and n:
    cur.execute(
      ops.D1_LEGACY_FLAG, [BODY_CAP]
    )
  return {"op": "flag_legacy", "found": n, "applied": bool(apply and n)}


def d1_orphan_edges(cur, apply: bool) -> dict:
  # FK_agent_memory_references_from/_to make a GUID-orphaned edge structurally
  # impossible. This asserts the invariant rather than pretending to repair it.
  n = cur.execute(ops.D1_ORPHAN_EDGES).fetchone()[0]
  return {"op": "orphan_edges", "found": n, "applied": False, "note": "assertion only; FK-guaranteed"}


# ── D2: queued operations (proposed, NEVER executed) ────────────────────────

def d2_proposals(cur) -> list[dict]:
  proposals: list[dict] = []

  for guid, title, blen in cur.execute(
    ops.D2_OVERSIZED, [BODY_CAP]
  ).fetchall():
    proposals.append({
      "op": "decompose", "subject": str(guid), "object": None, "trigger": "validate",
      "rationale": f"Body is {blen} chars, over the {BODY_CAP} cap. Split into atomic "
                   f"entries linked with edges. Cannot be UPDATEd until decomposed.",
      "title": title,
    })

  rows = cur.execute(
    ops.D2_DUPLICATE_CANDIDATES
  ).fetchall()
  by_hash: dict[str, list] = defaultdict(list)
  for guid, title, body in rows:
    by_hash[normalised_hash(body)].append((str(guid), title))
  for _h, group in by_hash.items():
    if len(group) > 1:
      keep = group[0]
      for dup_guid, dup_title in group[1:]:
        proposals.append({
          "op": "dedup", "subject": dup_guid, "object": keep[0], "trigger": "validate",
          "rationale": f"Body is byte-identical (whitespace/case normalised) to {keep[0][:8]} "
                       f"'{(keep[1] or '')[:60]}'. Merge and supersede.",
          "title": dup_title,
        })

  # §C3b: a session_summary is progress state that LINKS OUT. Zero outbound
  # edges means it is restating rather than citing — the narrative-aggregate
  # shape the FDD argues against.
  for guid, title in cur.execute(ops.D2_UNLINKED_SUMMARIES).fetchall():
    proposals.append({
      "op": "abstract", "subject": str(guid), "object": None, "trigger": "validate",
      "rationale": "session_summary with zero outbound edges. It should cite decisions "
                   "and specs, not restate them. Extract durable facts into their own "
                   "entries and link out.",
      "title": title,
    })

  # §A6b durability sweep — only where a document DEMONSTRABLY EXISTS to recover.
  #
  # V6b ("a spec without verbatim text is a summary") is right for a spec mined
  # out of a document. It is meaningless for a spec AUTHORED DIRECTLY in the
  # bank: much of the flicker and unity design was done in MCP only and never
  # existed as a file, so pub_source there is a provenance LABEL, not a path.
  #
  # Two heuristics were tried and both were wrong. Unfiltered gave 80 proposals,
  # ~75 unactionable. Requiring a path-shaped pub_source still gave 17, all
  # unity `docs/*.md` labels for documents that never existed in any repo.
  # String shape cannot answer this question — only the repo can.
  #
  # So: ask git. Propose only when the path actually has history in this repo.
  # A queue that is mostly noise is a queue nobody drains, which would quietly
  # disable the one durability check the FDD cares about.
  for guid, title, src in cur.execute(ops.D2_SPECS_WITHOUT_DOCUMENTS).fetchall():
    if not _has_git_history(str(src)):
      continue
    proposals.append({
      "op": "missing_document", "subject": str(guid), "object": None, "trigger": "validate",
      "rationale": f"kind='spec' with no verbatim document. pub_source={src!r}. Hunt the "
                   f"source in git history and load it, or mark fidelity 'unrecovered'.",
      "title": title,
    })

  return proposals


def enqueue(cur, proposals: list[dict], apply: bool) -> int:
  """Insert proposals, skipping any already pending.

  UX_ammq_open makes (op, subject, object) unique WHERE pending, so a nightly
  run cannot pile up duplicates of the same proposal — load-bearing given there
  is no scheduler deduplicating runs.
  """
  if not apply:
    return 0
  inserted = 0
  for p in proposals:
    exists = cur.execute(ops.QUEUE_EXISTS, [p["op"], p["subject"], p["subject"], p["object"], p["object"]]).fetchone()[0]
    if exists:
      continue
    cur.execute(ops.QUEUE_INSERT, [p["op"], p["subject"], p["object"], p["trigger"], p["rationale"][:2000]])
    inserted += 1
  return inserted


# ── D4: morning report ──────────────────────────────────────────────────────

def report(d1: list[dict], proposals: list[dict], inserted: int, apply: bool, quiet: bool) -> None:
  if quiet and not proposals and all(not r.get("found") and not r.get("drifted") for r in d1):
    return
  print("=" * 78)
  print("MEMORY SLEEP CYCLE — morning report" + ("" if apply else "   [DRY RUN — nothing written]"))
  print("=" * 78)
  print("\nD1 automatic operations")
  for r in d1:
    n = r.get("drifted", r.get("found", 0))
    mark = "applied" if r.get("applied") else ("clean" if not n else "PENDING --apply")
    print(f"  {r['op']:<22} {n:>5}   {mark}" + (f"   ({r['note']})" if r.get("note") else ""))

  print(f"\nD2 proposals — {len(proposals)} found, {inserted} newly queued")
  if not proposals:
    print("  (nothing to propose)")
  by_op: dict[str, list] = defaultdict(list)
  for p in proposals:
    by_op[p["op"]].append(p)
  for op, group in sorted(by_op.items()):
    print(f"\n  {op}  ({len(group)})")
    for p in group[:8]:
      print(f"    {p['subject'][:8]}  {(p['title'] or '')[:64]}")
      print(f"              {p['rationale'][:100]}")
    if len(group) > 8:
      print(f"    ... and {len(group) - 8} more")

  print("\n" + "-" * 78)
  print("Proposals are NEVER executed automatically. Review and decide with:")
  print("  memory_maintenance(op='list')")
  print("  memory_maintenance(op='apply'|'reject', queue_guid=..., rationale=...)")
  if not apply:
    print("\nRe-run with --apply to perform D1 repairs and enqueue these proposals.")


def main() -> None:
  ap = argparse.ArgumentParser(description="Memory sleep cycle (FDD-ORACLE-MEM-UNIFY-01 Part D)")
  ap.add_argument("--apply", action="store_true", help="Apply D1 repairs and enqueue D2 proposals")
  ap.add_argument("--quiet", action="store_true", help="Suppress output when there is nothing to say")
  args = ap.parse_args()

  conn = connect()
  cur = conn.cursor()
  try:
    d1 = [d1_recompute_counts(cur, args.apply),
          d1_flag_legacy(cur, args.apply),
          d1_orphan_edges(cur, args.apply)]
    proposals = d2_proposals(cur)
    inserted = enqueue(cur, proposals, args.apply)
    report(d1, proposals, inserted, args.apply, args.quiet)
  finally:
    conn.close()


if __name__ == "__main__":
  main()

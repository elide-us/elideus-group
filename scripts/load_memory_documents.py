"""Load the recovered v2.5 source documents into the memory document store.

Implements FDD-ORACLE-MEM-UNIFY-01 §4.0 B0.6 (step 3 of §7).

The 58 markdown documents migrated into the memory bank on 2026-07-20 were
deleted from the working tree by commit 8b76ead7 in the same change. The import
compressed them into pub_body prose at an overall ratio of 0.32 — 68% of the
source text was discarded — so the banked entries are summaries, not the
documents themselves. This script restores the verbatim bytes.

It does NOT read from a scratch directory. It extracts the blobs straight from
git at the pinned pre-deletion commit, so it is deterministic and reproducible
on any clone that has the tag:

    mem-unify-01/pre-doc-deletion  ->  ee22615e  (= 8b76ead7^)

Every file is verified byte-for-byte against `git show <commit>:<path>` before
it is loaded, and the sha256 recorded in pub_content_sha256 is computed from
those same bytes. pub_fidelity is 'verbatim' for everything this script loads;
it never writes 'reconstructed' or 'unrecovered'.

Documents are CONTENT-ADDRESSED: key_guid = UUID5(NS, 'document:' + sha256),
so identical bytes always resolve to one row. The entry <-> document relation
lives in agent_memory_entry_documents because it is many-to-many in both
directions — four source files back multiple entries, and ~10 entries cite two
or more documents (see the header of v0.13.8.0_memory_unify_foundation.sql).

pub_body is never read, written, or modified. Neither is pub_document once
written: re-running this script is a no-op for rows that already exist.

Usage:
    python scripts/load_memory_documents.py              # dry run, prints the plan
    python scripts/load_memory_documents.py --apply      # load
    python scripts/load_memory_documents.py --apply --project elideus-group
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import uuid

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT

load_dotenv(os.path.join(REPO_ROOT, ".env"))

# Pinned by `git tag mem-unify-01/pre-doc-deletion 8b76ead7^` during B0.
RECOVERY_TAG = "mem-unify-01/pre-doc-deletion"
DELETION_COMMIT = "8b76ead7"
SOURCE_REPO = "elideus-group"

# Memory-content UUID5 namespace, per FDD §A5. Distinct from the reflection
# namespace (...C0FFEE420B67) used by the migrations for schema registration
# rows. Change here only — every document key derives from this constant.
MEMORY_NAMESPACE = uuid.UUID("DECAFBAD-CAFE-FADE-BABE-C0FFEE420DAB")

# 'PATTERNS.md §5.4' / '§0/§6' — the section locator that follows a path.
SECTION_RE = re.compile(r"§\s*[0-9]+(?:\.[0-9]+)*(?:\s*/\s*§\s*[0-9]+(?:\.[0-9]+)*)*")


def connect() -> pyodbc.Connection:
  """Connect to the test database only.

  Deliberately does NOT fall back to AZURE_SQL_CONNECTION_STRING. Other scripts
  in this directory do, but that string points at the production database
  (elideus-group), which this effort is not authorised to touch — the whole FDD
  targets elideus-group-test. A silent fallback would mean an unset _DEV var
  quietly loads 58 documents and rewrites the graph in production. Fail instead.
  """
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV")
  if not dsn:
    raise RuntimeError(
      "Missing AZURE_SQL_CONNECTION_STRING_DEV (the elideus-group-test database). "
      "This script will not fall back to AZURE_SQL_CONNECTION_STRING — that is production."
    )
  # autocommit=True is required, not cosmetic. With autocommit=False pyodbc
  # opens an implicit transaction, so the explicit BEGIN below nests
  # (@@TRANCOUNT 2), COMMIT only decrements it to 1, and conn.close() rolls the
  # whole load back — while the script's own readback still reports success,
  # because a connection sees its own uncommitted writes. Matches
  # seed_workflows.py / seed_rpcdispatch.py.
  return pyodbc.connect(dsn, autocommit=True)


def git(*args: str) -> str:
  return subprocess.check_output(["git", *args], cwd=REPO_ROOT).decode("utf-8", "replace").strip()


def git_bytes(*args: str) -> bytes:
  return subprocess.check_output(["git", *args], cwd=REPO_ROOT)


def resolve_commit() -> str:
  """Prefer the pinned tag; fall back to the deletion commit's parent."""
  try:
    return git("rev-parse", f"{RECOVERY_TAG}^{{commit}}")
  except subprocess.CalledProcessError:
    print(f"  ! tag {RECOVERY_TAG} not found, falling back to {DELETION_COMMIT}^")
    return git("rev-parse", f"{DELETION_COMMIT}^")


def recover_documents(commit: str) -> dict[str, dict]:
  """Extract every file the deletion commit removed, at its pre-deletion state."""
  paths = [p for p in git("show", "--diff-filter=D", "--name-only", "--format=", DELETION_COMMIT).split("\n") if p]
  docs: dict[str, dict] = {}
  for path in paths:
    blob = git_bytes("show", f"{commit}:{path}")
    sha = hashlib.sha256(blob).hexdigest()
    docs[path] = {
      "path": path,
      "sha256": sha,
      "bytes": blob,
      "byte_length": len(blob),
      "key_guid": str(uuid.uuid5(MEMORY_NAMESPACE, f"document:{sha}")).upper(),
      "text": blob.decode("utf-8", "replace"),
    }
  return docs


def match_sources(pub_source: str, paths: list[str]) -> list[tuple[str, str | None]]:
  """Resolve a pub_source string to (path, section) pairs.

  Longest path first, consuming the matched span, so 'server/AGENTS.md' claims
  its text before a bare 'AGENTS.md' can match the same characters. Without
  this, all ten AGENTS.md files collapse onto whichever one is tested first.
  """
  if not pub_source:
    return []
  consumed = [False] * len(pub_source)
  hits: list[tuple[int, str, str | None]] = []
  for path in sorted(paths, key=len, reverse=True):
    start = 0
    while True:
      i = pub_source.find(path, start)
      if i < 0:
        break
      end = i + len(path)
      if any(consumed[i:end]):
        start = end
        continue
      # A bare basename must not match inside a longer path we do not carry.
      if i > 0 and (pub_source[i - 1].isalnum() or pub_source[i - 1] in "/\\_-"):
        start = end
        continue
      for k in range(i, end):
        consumed[k] = True
      tail = pub_source[end:end + 24]
      m = SECTION_RE.search(tail)
      hits.append((i, path, m.group(0).strip() if m else None))
      start = end
  hits.sort(key=lambda h: h[0])
  return [(p, s) for _, p, s in hits]


def load(apply: bool, project: str | None) -> None:
  commit = resolve_commit()
  branch = git("rev-parse", "--abbrev-ref", "HEAD")
  print(f"recovery commit : {commit}  (tag {RECOVERY_TAG})")
  print(f"deletion commit : {DELETION_COMMIT}")

  docs = recover_documents(commit)
  by_sha = {d["sha256"]: d for d in docs.values()}
  print(f"recovered       : {len(docs)} files, {sum(d['byte_length'] for d in docs.values())} bytes, "
        f"{len(by_sha)} distinct sha256")

  conn = connect()
  cursor = conn.cursor()
  try:
    sql = "SELECT key_guid, pub_kind, pub_source, pub_title FROM dbo.agent_memory_entries WHERE pub_source IS NOT NULL"
    params: list = []
    if project:
      sql += " AND pub_project = ?"
      params.append(project)
    entries = cursor.execute(sql, params).fetchall()
    print(f"entries w/source: {len(entries)}")

    paths = list(docs)
    links: list[tuple[str, str, str, str, str | None]] = []
    unmatched: list[tuple[str, str]] = []
    for key_guid, kind, pub_source, title in entries:
      matched = match_sources(pub_source or "", paths)
      if not matched:
        unmatched.append((str(key_guid)[:8], (pub_source or "")[:70]))
        continue
      for idx, (path, section) in enumerate(matched):
        role = "primary" if idx == 0 else "supporting"
        links.append((str(key_guid).upper(), kind, docs[path]["key_guid"], role, section))

    print(f"links resolved  : {len(links)} across {len({l[0] for l in links})} entries")
    print(f"entries unmatched: {len(unmatched)}")
    sections = [l for l in links if l[4]]
    print(f"section-scoped  : {len(sections)}  e.g. {[ (l[0], l[4]) for l in sections[:4] ]}")

    if not apply:
      print("\nDRY RUN — nothing written. Re-run with --apply.")
      for g, s in unmatched[:10]:
        print(f"  unmatched {g}  pub_source={s!r}")
      return

    cursor.execute("BEGIN TRANSACTION;")
    inserted_docs = 0
    for d in by_sha.values():
      existing = cursor.execute(
        "SELECT COUNT(*) FROM dbo.agent_memory_documents WHERE pub_content_sha256 = ?", [d["sha256"]]
      ).fetchone()[0]
      if existing:
        continue
      cursor.execute(
        """
        INSERT INTO dbo.agent_memory_documents
          (key_guid, pub_content_sha256, pub_document, pub_byte_length, pub_format,
           pub_source_path, pub_source_repo, pub_source_commit, pub_source_branch, pub_fidelity)
        VALUES (?, ?, ?, ?, N'markdown', ?, ?, ?, ?, N'verbatim');
        """,
        [d["key_guid"], d["sha256"], d["text"], d["byte_length"],
         d["path"], SOURCE_REPO, commit, branch],
      )
      inserted_docs += 1

    inserted_links = 0
    for entry_guid, kind, doc_guid, role, section in links:
      existing = cursor.execute(
        """
        SELECT COUNT(*) FROM dbo.agent_memory_entry_documents
         WHERE ref_entry_guid = ? AND ref_document_guid = ?
           AND ((pub_section IS NULL AND ? IS NULL) OR pub_section = ?)
        """,
        [entry_guid, doc_guid, section, section],
      ).fetchone()[0]
      if existing:
        continue
      cursor.execute(
        """
        INSERT INTO dbo.agent_memory_entry_documents
          (ref_entry_guid, pub_entry_kind, ref_document_guid, pub_role, pub_section)
        VALUES (?, ?, ?, ?, ?);
        """,
        [entry_guid, kind, doc_guid, role, section],
      )
      inserted_links += 1

    cursor.execute("COMMIT TRANSACTION;")
    print(f"\ninserted documents: {inserted_docs}")
    print(f"inserted links    : {inserted_links}")

    total, verbatim = cursor.execute(
      "SELECT COUNT(*), SUM(CASE WHEN pub_fidelity = N'verbatim' THEN 1 ELSE 0 END) FROM dbo.agent_memory_documents"
    ).fetchone()
    print(f"documents in bank : {total} ({verbatim} verbatim)")
  except Exception:
    try:
      cursor.execute("ROLLBACK TRANSACTION;")
    except Exception:
      pass
    raise
  finally:
    conn.close()


def verify() -> None:
  """Re-hash every stored document and compare against pub_content_sha256.

  This lives here rather than in the migration because pub_content_sha256 is
  the digest of the source file's UTF-8 bytes, while pub_document is NVARCHAR
  (UTF-16). HASHBYTES over CONVERT(VARCHAR(MAX), ...) hashes a codepage
  conversion and disagrees for any non-ASCII content — which is 55 of the 58
  documents. Round-tripping through Python encodes UTF-8 explicitly, so the
  comparison is against the same bytes the digest was taken over.

  Also re-reads the blob from git where a source commit is recorded, so a
  document that drifted from its origin is caught, not just one that drifted
  from its own recorded hash.
  """
  conn = connect()
  cursor = conn.cursor()
  try:
    rows = cursor.execute(
      """
      SELECT key_guid, pub_content_sha256, pub_byte_length, pub_source_path,
             pub_source_commit, pub_fidelity, pub_document
        FROM dbo.agent_memory_documents
      """
    ).fetchall()
    expected = len(recover_documents(resolve_commit()))
    print(f"documents in bank : {len(rows)}   (expected {expected})")

    # An empty table makes every check below trivially 0 and would otherwise
    # print PASS — a verifier that cannot fail is worse than no verifier.
    if len(rows) < expected:
      print(f"\nVERIFY: FAIL — {expected - len(rows)} document(s) missing. "
            f"Run: python scripts/load_memory_documents.py --apply")
      sys.exit(1)

    hash_bad, len_bad, git_bad, git_ok = [], [], [], 0
    for key_guid, sha, byte_len, path, commit, fidelity, document in rows:
      raw = document.encode("utf-8")
      actual = hashlib.sha256(raw).hexdigest()
      if actual != (sha or "").lower():
        hash_bad.append((str(key_guid)[:8], path, sha, actual))
      if len(raw) != byte_len:
        len_bad.append((str(key_guid)[:8], path, byte_len, len(raw)))
      if commit and path and fidelity == "verbatim":
        try:
          blob = git_bytes("show", f"{commit}:{path}")
          if hashlib.sha256(blob).hexdigest() == actual:
            git_ok += 1
          else:
            git_bad.append((str(key_guid)[:8], path, commit))
        except subprocess.CalledProcessError:
          git_bad.append((str(key_guid)[:8], path, f"{commit} (blob unreadable)"))

    print(f"hash mismatches   : {len(hash_bad)}")
    print(f"byte_length wrong : {len(len_bad)}")
    print(f"re-verified vs git: {git_ok} ok, {len(git_bad)} failed")
    for g, p, want, got in hash_bad[:10]:
      print(f"   HASH {g} {p}\n        stored={want}\n        actual={got}")
    for g, p, want, got in len_bad[:10]:
      print(f"   LEN  {g} {p}  stored={want} actual={got}")
    for g, p, c in git_bad[:10]:
      print(f"   GIT  {g} {p}  @{c}")

    ok = not (hash_bad or len_bad or git_bad)
    print("\nVERIFY: PASS — every document is byte-identical to its source." if ok else "\nVERIFY: FAIL")
    if not ok:
      sys.exit(1)
  finally:
    conn.close()


def main() -> None:
  parser = argparse.ArgumentParser(description="Load recovered v2.5 source documents into the memory document store")
  parser.add_argument("--apply", action="store_true", help="Write to the database (default is a dry run)")
  parser.add_argument("--verify", action="store_true", help="Re-hash stored documents against git and their digests")
  parser.add_argument("--project", default=None, help="Restrict entry linking to one project slug")
  args = parser.parse_args()
  if args.verify:
    verify()
    return
  load(apply=args.apply, project=args.project)


if __name__ == "__main__":
  main()

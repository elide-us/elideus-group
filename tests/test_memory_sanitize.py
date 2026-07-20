"""Unit tests for the write-path leak sanitiser (MemoryModule._sanitize_body_tags).

Pure logic — no DB. Reproduces the real tool-call boundary leak where a store's
`tags` argument bled into `body` (`…body</body>\\n<parameter name="tags">tags",`)
with `tags` arriving None, and verifies the sanitiser strips the trailing
artifact and recovers the tags WITHOUT touching mid-text mentions or clean input.
"""

import pytest

from server.modules.memory_module import MemoryModule

sanitize = MemoryModule._sanitize_body_tags


# ── no-ops ──────────────────────────────────────────────────────────────────

def test_clean_body_is_untouched():
  body = "A normal body.\nWith two lines and a `code` span. See [[ABC123]]."
  assert sanitize(body, "a b c") == (body, "a b c")


def test_none_and_empty_body_are_noops():
  assert sanitize(None, "x") == (None, "x")
  assert sanitize("", "x") == ("", "x")


# ── mild variant: bare trailing </body>, tags already correct ───────────────

def test_mild_trailing_body_close_is_stripped_tags_kept():
  body, tags = sanitize("real content.</body>\n", "keep me")
  assert body == "real content."
  assert tags == "keep me"


def test_mild_trailing_body_close_no_newline():
  body, tags = sanitize("real content.</body>", None)
  assert body == "real content."
  assert tags is None


# ── severe variant: tags leaked into body, real tags param lost (None) ──────

def test_severe_leak_recovers_tags():
  raw = 'the real body.</body>\n<parameter name="tags">alpha beta gamma'
  body, tags = sanitize(raw, None)
  assert body == "the real body."
  assert tags == "alpha beta gamma"


def test_severe_leak_with_trailing_json_junk_is_cleaned():
  # This is the exact shape stored for 815CCE47.
  raw = ('...Purely additive; no migration.</body>\n'
         '<parameter name="tags">elideus-group mcp memory graph references '
         'links traversal rpc api schema change-list spec",')
  body, tags = sanitize(raw, None)
  assert body == "...Purely additive; no migration."
  assert tags == ("elideus-group mcp memory graph references links traversal "
                  "rpc api schema change-list spec")


def test_leaked_tags_do_not_overwrite_explicit_tags():
  raw = 'body text.</body>\n<parameter name="tags">leaked ones'
  body, tags = sanitize(raw, "caller supplied")
  assert body == "body text."
  assert tags == "caller supplied"     # explicit tags win; leaked ones ignored


def test_parameter_invoke_close_variant():
  body, tags = sanitize("body here.</parameter></invoke>", None)
  assert body == "body here."
  assert tags is None


# ── the safety property: mid-text mentions are NOT stripped ─────────────────

def test_midtext_mention_preserved_only_trailing_artifact_stripped():
  # A bug-writeup body that legitimately quotes the artifact mid-text AND has a
  # trailing leaked </body> appended. Only the trailing one must go.
  body_real = ('The leak looks like `</body>\\n<parameter name="tags">x` in the '
               'body, and pub_tags ends up NULL. See the writeup for details.')
  raw = body_real + "</body>\n"
  body, tags = sanitize(raw, "bug memory-service")
  assert body == body_real            # the quoted mid-text </body> survives
  assert tags == "bug memory-service"


def test_body_that_is_only_boundary_junk_is_not_destroyed():
  # Degenerate: stripping would leave nothing — keep the original rather than
  # persist an empty body.
  raw = '</body>\n<parameter name="tags">only junk'
  assert sanitize(raw, None) == (raw, None)

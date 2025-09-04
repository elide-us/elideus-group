from scripts.run_tests import _next_build

def test_patch_version_does_not_reset_build():
  assert _next_build('v0.5.2.20', 'v0.5.1.20') == 21

def test_minor_version_resets_build():
  assert _next_build('v0.6.0.5', 'v0.5.9.100') == 1

def test_major_version_resets_build():
  assert _next_build('v1.0.0.7', 'v0.9.9.3') == 1
